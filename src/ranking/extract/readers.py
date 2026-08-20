"""Reading the CVM files into typed tables.

Two conventions worth stating once:

- Everything is read as text first and cast explicitly afterwards. Letting a
  CSV reader guess types means a column silently changing type when next
  month's file happens to contain an empty value in a different place.
- Column names keep the source's own vocabulary in Portuguese (`cnpj_classe`,
  `valor_cota`). Translating domain terms would add a layer of indirection
  between the code and the published field it came from, for no gain.
"""

from __future__ import annotations

import io
from pathlib import Path

import polars as pl

from ranking.transform import normalize


class UnsupportedLayoutError(ValueError):
    """The file is not in the layout this reader understands.

    The CVM daily report has had three layouts. Since January 2024 it is
    published per *class*, with `CNPJ_FUNDO_CLASSE`. Code written for the older
    per-fund layout joins on a key that does not exist in the registry and
    produces an empty or wrong result **without raising anything**, so the
    reader refuses the old layout loudly instead.
    """


# The class-grain layout, in use since 2024-01.
_DAILY_REPORT_L3: dict[str, str] = {
    "TP_FUNDO_CLASSE": "tipo_classe",
    "CNPJ_FUNDO_CLASSE": "cnpj_classe",
    "ID_SUBCLASSE": "id_subclasse",
    "DT_COMPTC": "data",
    "VL_TOTAL": "valor_total",
    "VL_QUOTA": "valor_cota",
    "VL_PATRIM_LIQ": "patrimonio_liquido",
    "CAPTC_DIA": "captacao",
    "RESG_DIA": "resgate",
    "NR_COTST": "cotistas",
}

_REGISTRY_CLASS: dict[str, str] = {
    "ID_Registro_Fundo": "id_registro_fundo",
    "ID_Registro_Classe": "id_registro_classe",
    "CNPJ_Classe": "cnpj_classe",
    "Tipo_Classe": "tipo_classe",
    "Denominacao_Social": "denominacao_social",
    "Situacao": "situacao",
    # Deliberately not called `data_inicio`: it is the resolution-175
    # adaptation date, and naming it honestly stops it being used as an age.
    "Data_Inicio": "data_adaptacao_rcvm175",
    "Classificacao": "classificacao",
    "Classificacao_Anbima": "classificacao_anbima",
    "Indicador_Desempenho": "indicador_desempenho",
    "Forma_Condominio": "forma_condominio",
    "Exclusivo": "exclusivo",
    "Publico_Alvo": "publico_alvo",
    "Tributacao_Longo_Prazo": "tributacao_longo_prazo",
    "Patrimonio_Liquido": "patrimonio_liquido_registro",
}

_REGISTRY_FUND: dict[str, str] = {
    "ID_Registro_Fundo": "id_registro_fundo",
    "CNPJ_Fundo": "cnpj_fundo",
    "Denominacao_Social": "denominacao_social_fundo",
    "Data_Constituicao": "data_constituicao",
    "Situacao": "situacao_fundo",
    "Administrador": "administrador",
    "Gestor": "gestor",
}


def read_latin1_csv(path: Path, separator: str = ";") -> pl.DataFrame:
    """Read a CVM CSV as text.

    The files are latin-1 with a semicolon separator, and neither is declared
    anywhere machine-readable. Reading them as UTF-8 mangles every accented
    fund name, which is most of them.
    """
    decoded = path.read_bytes().decode("latin-1").encode("utf-8")
    return pl.read_csv(
        io.BytesIO(decoded),
        separator=separator,
        infer_schema_length=0,  # everything as text; casting is explicit below
        truncate_ragged_lines=True,
    )


def _select_and_rename(frame: pl.DataFrame, mapping: dict[str, str]) -> pl.DataFrame:
    present = [column for column in mapping if column in frame.columns]
    return frame.select(present).rename({column: mapping[column] for column in present})


def _cast_present(frame: pl.DataFrame, casts: dict[str, pl.Expr]) -> pl.DataFrame:
    """Apply only the casts whose column actually arrived.

    The CVM adds and removes columns between releases. Casting unconditionally
    turns a missing optional field into a crash on line one, which is a bad
    trade for something the pipeline can carry on without.
    """
    return frame.with_columns(
        [expression for column, expression in casts.items() if column in frame.columns]
    )


def _deduplicate(frame: pl.DataFrame, key: str) -> pl.DataFrame:
    """Collapse repeated keys, keeping the last occurrence.

    `registro_fundo.csv` ships 1,046 fund ids more than once, with byte
    identical rows. Joining against it multiplies every class that belongs to
    one of those funds, inflating the universe by roughly two percent — small
    enough to sit inside the funnel tolerance and therefore invisible.
    Later rows win, on the assumption that corrections are appended.
    """
    if key not in frame.columns:
        return frame
    return frame.unique(subset=[key], keep="last", maintain_order=True)


def _clean_cnpj(column: str) -> pl.Expr:
    """Strip formatting only. Whether the result is a real CNPJ is a question
    for the contract layer, which can quarantine the row with a reason."""
    return pl.col(column).str.replace_all(r"\D", "").alias(column)


def read_daily_report(path: Path) -> pl.DataFrame:
    """One row per class per day: quota, net assets, shareholders, flows."""
    frame = read_latin1_csv(path)

    required = ("CNPJ_FUNDO_CLASSE", "ID_SUBCLASSE")
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise UnsupportedLayoutError(
            f"{path.name} is not the class-grain layout: missing {missing}. "
            "Files published before 2024-01 use CNPJ_FUNDO and cannot be joined "
            "against the RCVM 175 registry without an explicit adapter."
        )

    frame = _select_and_rename(frame, _DAILY_REPORT_L3)

    # Subclass rows repeat the class series. Keeping both double-counts a fund.
    frame = frame.filter(
        pl.col("id_subclasse").is_null() | (pl.col("id_subclasse").str.strip_chars() == "")
    ).drop("id_subclasse")

    return frame.with_columns(
        _clean_cnpj("cnpj_classe"),
        pl.col("data").str.to_date("%Y-%m-%d", strict=False),
        pl.col("valor_total").cast(pl.Float64, strict=False),
        pl.col("valor_cota").cast(pl.Float64, strict=False),
        pl.col("patrimonio_liquido").cast(pl.Float64, strict=False),
        pl.col("captacao").cast(pl.Float64, strict=False),
        pl.col("resgate").cast(pl.Float64, strict=False),
        pl.col("cotistas").cast(pl.Int64, strict=False),
    )


def read_registry_classes(path: Path) -> pl.DataFrame:
    """The class registry: classification, target investor, open or closed."""
    frame = _select_and_rename(read_latin1_csv(path), _REGISTRY_CLASS)
    frame = _cast_present(
        frame,
        {
            "cnpj_classe": _clean_cnpj("cnpj_classe"),
            "data_adaptacao_rcvm175": pl.col("data_adaptacao_rcvm175").str.to_date(
                "%Y-%m-%d", strict=False
            ),
            "patrimonio_liquido_registro": pl.col("patrimonio_liquido_registro").cast(
                pl.Float64, strict=False
            ),
        },
    )
    return _deduplicate(frame, "id_registro_classe")


def read_registry_funds(path: Path) -> pl.DataFrame:
    """The fund registry, which is where the real constitution date lives."""
    frame = _select_and_rename(read_latin1_csv(path), _REGISTRY_FUND)
    frame = _cast_present(
        frame,
        {
            "cnpj_fundo": _clean_cnpj("cnpj_fundo"),
            "data_constituicao": pl.col("data_constituicao").str.to_date("%Y-%m-%d", strict=False),
        },
    )
    return _deduplicate(frame, "id_registro_fundo")


def read_registry(class_path: Path, fund_path: Path) -> pl.DataFrame:
    """Classes with their parent fund attached.

    The join exists mainly to carry `data_constituicao` down to class level:
    it is the only trustworthy source of a fund's age.
    """
    classes = read_registry_classes(class_path)
    funds = read_registry_funds(fund_path)
    joined = classes.join(funds, on="id_registro_fundo", how="left")

    # A left join must never produce more rows than it started with. If it
    # does, a key is repeated on the right and the universe is silently
    # inflated — the exact failure this reader deduplicates to prevent.
    if len(joined) != len(classes):
        raise ValueError(
            f"registry join changed the row count: {len(classes)} classes became "
            f"{len(joined)}. A fund id is repeated in {fund_path.name}."
        )
    return joined


def fund_age_years(frame: pl.DataFrame, as_of: object) -> pl.DataFrame:
    """Attach an `idade_anos` column derived from the constitution date."""
    return frame.with_columns(
        (
            (pl.lit(as_of).cast(pl.Date) - pl.col("data_constituicao")).dt.total_days()
            / normalize.DAYS_IN_YEAR
        ).alias("idade_anos")
    )
