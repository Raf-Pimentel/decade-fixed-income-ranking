"""The command line.

Deliberately thin. Everything it does, `pipeline.run` does — the command is a
convenience, not the interface. Another team importing the function gets the
same behaviour without shelling out.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Annotated

import typer

from ranking import pipeline

app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def main(
    reference_date: Annotated[
        dt.datetime,
        typer.Option("--reference-date", formats=["%Y-%m-%d"], help="The date to rank as of."),
    ],
    config_dir: Annotated[Path, typer.Option(help="Where the YAML lives.")] = Path("configs"),
    output_dir: Annotated[Path, typer.Option(help="Where to write the results.")] = Path("saida"),
    lookback_months: Annotated[
        int | None, typer.Option(help="Override the scoring window.")
    ] = None,
    simulations: Annotated[
        int | None, typer.Option(help="Override how many times the ranking is rebuilt.")
    ] = None,
    offline: Annotated[
        bool, typer.Option(help="Read from a local slice instead of downloading.")
    ] = False,
    input_dir: Annotated[Path | None, typer.Option(help="Local slice, with --offline.")] = None,
) -> None:
    """Rank Brazilian fixed-income funds as of a reference date."""
    result = pipeline.run(
        reference_date=reference_date.date(),
        config_dir=config_dir,
        output_dir=output_dir,
        input_dir=input_dir,
        offline=offline,
        lookback_months=lookback_months,
        simulations=simulations,
    )

    verdict = "dentro do baseline" if result.funnel.ok else "FORA DO BASELINE"
    typer.echo(f"Funil de qualidade: {verdict}.")
    typer.echo(f"Linhas em quarentena: {result.quarantined_share:.2%}.")
    for profile in result.payload.profiles:
        typer.echo(f"\n{profile.label} — {profile.eligible_universe_size} fundos elegíveis")
        for fund in profile.top:
            typer.echo(
                f"  {fund.rank}. {fund.name[:52]:<52} "
                f"nota {fund.score:5.1f}  aparição {fund.appearance_rate:.0%}"
            )
    typer.echo(f"\nEscrito em {result.output_dir}/")

    if not result.funnel.ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":  # pragma: no cover
    app()
