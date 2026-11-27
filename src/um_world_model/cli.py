"""Command-line interface for the Phase 0/1 experiment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .evaluate import evaluate_run
from .ingest import ingest_town
from .normalize import normalize_run
from .resolve import resolve_run
from .sources import load_source_catalog, repository_root, validate_ontology

app = typer.Typer(
    no_args_is_help=True, help="United Main Phase 0/1 public-data experiment."
)
ROOT = repository_root()
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_SEED = ROOT / "evaluation" / "benchmark-businesses.csv"
DEFAULT_REPORT_DIR = ROOT / "reports" / "gate-a"


def default_data_dir() -> Path:
    return DEFAULT_DATA_DIR


def latest_manifest(data_dir: Path) -> Path:
    pointer = data_dir / "latest-run.txt"
    if not pointer.exists():
        raise typer.BadParameter(
            "no ingestion run exists; run `umwm ingest-town` first"
        )
    return (
        data_dir
        / "runs"
        / pointer.read_text(encoding="utf-8").strip()
        / "manifest.json"
    )


@app.command()
def status() -> None:
    """Validate Phase 0 contracts and report implementation status."""
    catalog = load_source_catalog()
    ontology = validate_ontology()
    typer.echo(
        json.dumps(
            {
                "status": "phase_0_1_implemented",
                "catalog_version": catalog["version"],
                "ontology_version": ontology["version"],
                "town": catalog["town"],
            },
            sort_keys=True,
        )
    )


@app.command("sources")
def sources_list(phase: int | None = typer.Option(None, min=0)) -> None:
    """List registered sources, optionally through a maximum phase."""
    catalog = load_source_catalog()
    for source in catalog["sources"]:
        if phase is None or source["phase"] <= phase:
            typer.echo(f"{source['id']}\tphase={source['phase']}\t{source['url']}")


@app.command("ingest-town")
def ingest_town_command(
    town: Annotated[str, typer.Option()] = "Stoneham",
    state: Annotated[str, typer.Option()] = "MA",
    data_dir: Annotated[Path, typer.Option()] = DEFAULT_DATA_DIR,
) -> None:
    """Ingest official address and parcel records with raw evidence."""
    path = ingest_town(data_dir=data_dir, town=town, state=state)
    typer.echo(path)


@app.command("normalize")
def normalize_command(
    manifest: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    data_dir: Annotated[Path, typer.Option()] = DEFAULT_DATA_DIR,
) -> None:
    """Normalize the latest verified raw run to Parquet contracts."""
    manifest_path = manifest or latest_manifest(data_dir)
    addresses, parcels = normalize_run(manifest_path)
    typer.echo(f"addresses={addresses}")
    typer.echo(f"parcels={parcels}")


@app.command("resolve")
def resolve_command(
    manifest: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    data_dir: Annotated[Path, typer.Option()] = DEFAULT_DATA_DIR,
) -> None:
    """Resolve addresses to parcels; fuzzy matches remain candidates only."""
    manifest_path = manifest or latest_manifest(data_dir)
    normalized = manifest_path.parent / "normalized"
    output = resolve_run(
        normalized / "addresses.parquet", normalized / "parcels.parquet"
    )
    typer.echo(output)


@app.command("evaluate")
def evaluate_command(
    manifest: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    data_dir: Annotated[Path, typer.Option()] = DEFAULT_DATA_DIR,
    seed: Annotated[Path, typer.Option()] = DEFAULT_SEED,
    reference: Annotated[Path | None, typer.Option()] = None,
    output_dir: Annotated[Path, typer.Option()] = DEFAULT_REPORT_DIR,
) -> None:
    """Evaluate Gate A without treating discovery seeds as ground truth."""
    manifest_path = manifest or latest_manifest(data_dir)
    normalized = manifest_path.parent / "normalized"
    report = evaluate_run(
        normalized / "addresses.parquet",
        normalized / "resolutions.jsonl",
        seed,
        output_dir,
        reference,
    )
    typer.echo(report)


if __name__ == "__main__":
    app()
