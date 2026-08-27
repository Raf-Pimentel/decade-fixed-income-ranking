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

import datetime as dt
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
    # "S" marks a class that invests through other funds rather than holding
    # assets directly. The registry says so outright, which is better than
    # guessing from the name, and it is what decides whether a fee can be
    # measured against the fund behind it.
    "Classe_Cotas": "classe_cotas",
    "Indicador_Desempenho": "indicador_desempenho",
    "Forma_Condominio": "forma_condominio",
    "Exclusivo": "exclusivo",
    "Publico_Alvo": "publico_alvo",
    "Tributacao_Longo_Prazo": "tributacao_longo_prazo",
    "Patrimonio_Liquido": "patrimonio_liquido_registro",
}

_STATEMENT: dict[str, str] = {
    "CNPJ_FUNDO_CLASSE": "cnpj_classe",
    "DT_COMPTC": "data",
    "TAXA_ADM": "taxa_adm",
    "TAXA_PERFM": "taxa_performance",
    "QT_DIA_CONVERSAO_COTA": "dias_conversao",
    "QT_DIA_PAGTO_RESGATE": "dias_pagamento",
    "TP_DIA_PAGTO_RESGATE": "tipo_dia_prazo",
    "APLIC_MIN": "aplicacao_minima",
    "PUBLICO_ALVO": "publico_alvo_extrato",
    "CLASSE_ANBIMA": "classe_anbima_extrato",
}

_FACTSHEET: dict[str, str] = {
    "CNPJ_FUNDO_CLASSE": "cnpj_classe",
    "ID_SUBCLASSE": "id_subclasse",
    "DT_COMPTC": "data",
    "TAXA_ADM": "taxa_adm",
    "TAXA_PERFM": "taxa_performance",
    # The factsheet spells the redemption columns differently from the
    # statement. Same idea, different names, a reminder that these are two
    # separate filings, not two copies of one.
    "QT_DIA_CONVERSAO_COTA_RESGATE": "dias_conversao",
    "QT_DIA_PAGTO_RESGATE": "dias_pagamento",
    "TP_DIA_PAGTO_RESGATE": "tipo_dia_prazo",
    "INVEST_INICIAL_MIN": "aplicacao_minima",
    "PUBLICO_ALVO": "publico_alvo_lamina",
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

    Quoting is disabled on purpose. The CVM never quotes fields, and every
    line carries the same number of semicolons either way. But its free-text
    columns do contain loose double quotes: `extrato_fi_2025.csv` has 194 of
    them, in investment-policy prose. A parser that reads them as delimiters
    opens a quoted region, swallows every newline until the next quote, and
    dies with "CSV malformed" a third of the way through a 12 MB file.
    """
    decoded = path.read_bytes().decode("latin-1").encode("utf-8")
    return pl.read_csv(
        io.BytesIO(decoded),
        separator=separator,
        quote_char=None,
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
    one of those funds, inflating the universe by roughly two percent. Small
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
    # inflated. That is the failure this reader deduplicates to prevent.
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


def read_statement(path: Path) -> pl.DataFrame:
    """Fees, redemption terms and minimum investment, from the CVM statement.

    Percentages are converted to fractions on the way in. The file says `0.20`
    meaning a fifth of a percent a year; carrying that through as `0.20` would
    make the cheapest funds in the country look like they charge twenty
    percent, and the cost weight is the largest one in the retail profile.
    """
    frame = _select_and_rename(read_latin1_csv(path), _STATEMENT)
    frame = _cast_present(
        frame,
        {
            "cnpj_classe": _clean_cnpj("cnpj_classe"),
            "data": pl.col("data").str.to_date("%Y-%m-%d", strict=False),
            "taxa_adm": pl.col("taxa_adm").cast(pl.Float64, strict=False) / 100,
            "taxa_performance": pl.col("taxa_performance").cast(pl.Float64, strict=False) / 100,
            "dias_conversao": pl.col("dias_conversao").cast(pl.Int64, strict=False),
            "dias_pagamento": pl.col("dias_pagamento").cast(pl.Int64, strict=False),
            "aplicacao_minima": pl.col("aplicacao_minima").cast(pl.Float64, strict=False),
        },
    )
    # What the client waits for is the whole thing: days until the quota is
    # struck, plus days until the money arrives.
    #
    # And the two are not always quoted in the same unit. `TP_DIA_PAGTO_RESGATE`
    # says whether the term is in business days or calendar days, and a fund
    # quoting "5 business days" makes the client wait a week. Treating the two
    # as interchangeable would flatter every fund that quotes business days,
    # which matters, because redemption speed carries the second-heaviest
    # weight in the retail profile.
    return _with_redemption_days(frame)


def _with_redemption_days(frame: pl.DataFrame) -> pl.DataFrame:
    """Total calendar days between asking for the money and receiving it.

    Two filings, one meaning. And the unit is not always the same:
    `TP_DIA_PAGTO_RESGATE` says whether the term is quoted in business days or
    calendar days, and a fund quoting "5 business days" makes the client wait a
    week. Treating the two as interchangeable would flatter every fund that
    quotes business days, which matters because redemption speed carries the
    second-heaviest weight in the retail profile.
    """
    raw_days = pl.col("dias_conversao").fill_null(0) + pl.col("dias_pagamento").fill_null(0)
    business = (
        pl.col("tipo_dia_prazo").str.to_uppercase().str.contains("TEIS").fill_null(False)
        if "tipo_dia_prazo" in frame.columns
        # If the source stops publishing the unit, assume calendar days: that
        # under-states nobody's liquidity, whereas assuming business days would
        # penalise every fund for a column we simply did not receive.
        else pl.lit(False)
    )
    return frame.with_columns(
        pl.when(business)
        .then((raw_days * 7 / 5).ceil())
        .otherwise(raw_days)
        .cast(pl.Int64)
        .alias("dias_resgate")
    )


def read_factsheet(path: Path) -> pl.DataFrame:
    """Fees and terms from the factsheet, which retail funds must publish.

    This is what lifts fee coverage from roughly seventy percent of the
    rankable universe to nearly all of the retail half of it.
    """
    frame = _select_and_rename(read_latin1_csv(path), _FACTSHEET)
    if "id_subclasse" in frame.columns:
        # Same trap as the daily report: a subclass row repeats its class.
        frame = frame.filter(
            pl.col("id_subclasse").is_null() | (pl.col("id_subclasse").str.strip_chars() == "")
        ).drop("id_subclasse")
    frame = _cast_present(
        frame,
        {
            "cnpj_classe": _clean_cnpj("cnpj_classe"),
            "data": pl.col("data").str.to_date("%Y-%m-%d", strict=False),
            "taxa_adm": pl.col("taxa_adm").cast(pl.Float64, strict=False) / 100,
            "taxa_performance": pl.col("taxa_performance").cast(pl.Float64, strict=False) / 100,
            "dias_conversao": pl.col("dias_conversao").cast(pl.Int64, strict=False),
            "dias_pagamento": pl.col("dias_pagamento").cast(pl.Int64, strict=False),
            "aplicacao_minima": pl.col("aplicacao_minima").cast(pl.Float64, strict=False),
        },
    )
    return _with_redemption_days(frame)


_INVESTOR_PROFILE = {
    "CNPJ_FUNDO_CLASSE": "cnpj_classe",
    "NR_COTST_PF_VAREJO": "cotistas_pf_varejo",
    "NR_COTST_PF_PB": "cotistas_pf_private",
    "NR_COTST_DISTRIB": "cotistas_distribuidor",
}


def read_investor_profile(path: Path) -> pl.DataFrame:
    """Who actually holds each class, counted rather than declared.

    Only the three columns that answer one question: is a person inside this
    fund? Individuals are reported in two buckets, retail and private banking,
    and money that arrives through a broker is reported as one distributor
    line rather than as the people behind it. Those three added together are
    the evidence; the remaining hundred columns describe companies, pension
    schemes and insurers, and are not read.
    """
    frame = _select_and_rename(read_latin1_csv(path), _INVESTOR_PROFILE)
    frame = _cast_present(
        frame,
        {
            "cnpj_classe": _clean_cnpj("cnpj_classe"),
            "cotistas_pf_varejo": pl.col("cotistas_pf_varejo").cast(pl.Float64, strict=False),
            "cotistas_pf_private": pl.col("cotistas_pf_private").cast(pl.Float64, strict=False),
            "cotistas_distribuidor": pl.col("cotistas_distribuidor").cast(pl.Float64, strict=False),
        },
    )
    return frame.with_columns(
        (
            pl.col("cotistas_pf_varejo").fill_null(0.0)
            + pl.col("cotistas_pf_private").fill_null(0.0)
        ).alias("cotistas_pf"),
        pl.col("cotistas_distribuidor").fill_null(0.0).alias("cotistas_distribuidor"),
    ).select("cnpj_classe", "cotistas_pf", "cotistas_distribuidor")


_HOLDINGS = {
    "CNPJ_FUNDO_CLASSE": "cnpj_classe",
    "CNPJ_FUNDO_CLASSE_COTA": "cnpj_investido",
    "VL_MERC_POS_FINAL": "valor",
}


def read_holdings(path: Path) -> pl.DataFrame:
    """Which fund each class holds, and how much of it.

    Block 2 of the portfolio composition file is the one that lists positions
    in other funds, which is the only place the CVM names the fund behind a
    feeder class. That link is what makes a fee measurable instead of merely
    declared: see `ranking.transform.fees`.

    Rows without a named fund are dropped rather than kept as unknown. A
    position the file cannot identify is not a master, and carrying it forward
    would only dilute the share that decides whether a class is a wrapper.
    """
    frame = _select_and_rename(read_latin1_csv(path), _HOLDINGS)
    frame = _cast_present(
        frame,
        {
            "cnpj_classe": _clean_cnpj("cnpj_classe"),
            "cnpj_investido": _clean_cnpj("cnpj_investido"),
            "valor": pl.col("valor").cast(pl.Float64, strict=False),
        },
    )
    return frame.filter(
        pl.col("cnpj_investido").is_not_null()
        & (pl.col("cnpj_investido").str.len_chars() == 14)
        & pl.col("valor").is_not_null()
    )


TERM_COLUMNS = ["cnpj_classe", "taxa_adm", "dias_resgate", "aplicacao_minima"]


def combine_terms(statement: pl.DataFrame, factsheet: pl.DataFrame) -> pl.DataFrame:
    """One set of terms per fund, with the source recorded.

    The statement wins where both filings exist: it is the more formal one. The
    factsheet fills the gaps, which is most of retail.

    `fonte_taxa` is not bookkeeping. The delivery tells a client what a fund
    costs, and whoever reads it is entitled to know which filing that number
    came from.
    """

    def _prepare(frame: pl.DataFrame, source: str) -> pl.DataFrame:
        if frame.is_empty():
            return frame.select(TERM_COLUMNS).with_columns(pl.lit(source).alias("fonte_taxa"))
        return (
            frame.select(TERM_COLUMNS)
            .filter(pl.col("taxa_adm").is_not_null() & pl.col("dias_resgate").is_not_null())
            .unique(subset=["cnpj_classe"], keep="last", maintain_order=True)
            .with_columns(pl.lit(source).alias("fonte_taxa"))
        )

    primary = _prepare(statement, "EXTRATO")
    fallback = _prepare(factsheet, "LAMINA").join(
        primary.select("cnpj_classe"), on="cnpj_classe", how="anti"
    )
    return pl.concat([primary, fallback])


def statement_in_force(frame: pl.DataFrame, reference_date: dt.date) -> pl.DataFrame:
    """The statement that was in force on the reference date, one per fund.

    Taking the most recent statement instead would describe a December 2025
    fund with terms filed in 2026, which is exactly the kind of leak that makes
    a backtest look better than the method really is.
    """
    return (
        frame.filter(pl.col("data").is_not_null() & (pl.col("data") <= reference_date))
        .sort("cnpj_classe", "data")
        .group_by("cnpj_classe", maintain_order=True)
        .last()
    )


def read_cdi(path: Path) -> pl.DataFrame:
    """The Central Bank's daily CDI series, as fractions.

    Two conversions, both silent if wrong. The file publishes percent per day,
    so 0.055 means 0.055%. Carrying it through as 5.5% compounds to something
    absurd over a year. And the dates are day-first: `05/12/2025` is the fifth
    of December, and reading it month-first would fetch a real but wrong
    window.
    """
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    frame = pl.DataFrame(payload, schema={"data": pl.String, "valor": pl.String})
    return (
        frame.with_columns(
            pl.col("data").str.to_date("%d/%m/%Y", strict=False),
            (pl.col("valor").cast(pl.Float64, strict=False) / 100).alias("taxa"),
        )
        .drop("valor")
        .sort("data")
    )
