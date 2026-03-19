from __future__ import annotations

import click


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Email File Ingestion Pipeline"""
    if ctx.invoked_subcommand is None:
        _interactive_menu()


def _interactive_menu() -> None:
    """Show interactive terminal menu when no subcommand is given."""
    try:
        from simple_term_menu import TerminalMenu
    except ImportError:
        click.echo("simple-term-menu not installed. Use direct commands instead.")
        click.echo("  email-ingest run --input-dir <path> --mode backfill")
        return

    options = [
        "[1] Run Pipeline (backfill)",
        "[2] Run Pipeline (incremental)",
        "[3] Show Status",
        "[4] Exit",
    ]
    menu = TerminalMenu(options, title="\n  Email File Ingestion Pipeline\n")
    choice = menu.show()

    if choice == 0:
        input_dir = click.prompt("Input directory", default="./_assignment/test_data")
        output_dir = click.prompt("Output directory", default="./output")
        _run_pipeline(input_dir, output_dir, "./pipeline_state.db", "backfill")
    elif choice == 1:
        input_dir = click.prompt("Input directory", default="./_assignment/test_data")
        output_dir = click.prompt("Output directory", default="./output")
        _run_pipeline(input_dir, output_dir, "./pipeline_state.db", "incremental")
    elif choice == 2:
        _show_status("./pipeline_state.db")
    elif choice == 3:
        click.echo("Bye!")


@cli.command()
@click.option("--input-dir", required=True, help="Path to input directory (simulated bucket)")
@click.option("--output-dir", default="./output", help="Path to output directory")
@click.option("--state-db", default="./pipeline_state.db", help="Path to SQLite state DB")
@click.option(
    "--mode",
    type=click.Choice(["backfill", "incremental"]),
    default="backfill",
    help="Pipeline mode",
)
def run(input_dir: str, output_dir: str, state_db: str, mode: str) -> None:
    """Run the ingestion pipeline."""
    _run_pipeline(input_dir, output_dir, state_db, mode)


@cli.command()
@click.option("--state-db", default="./pipeline_state.db", help="Path to SQLite state DB")
def status(state_db: str) -> None:
    """Show pipeline state and last run info."""
    _show_status(state_db)


def _run_pipeline(input_dir: str, output_dir: str, state_db: str, mode: str) -> None:
    from src.pipeline import run_pipeline

    click.echo(f"\nRunning pipeline ({mode} mode)...")
    click.echo(f"  Input:  {input_dir}")
    click.echo(f"  Output: {output_dir}")
    click.echo()

    result = run_pipeline(input_dir, output_dir, state_db, mode)

    click.echo("\n--- Pipeline Summary ---")
    click.echo(f"  Run ID:       {result.run_id}")
    click.echo(f"  Mode:         {result.mode}")
    click.echo(f"  Discovered:   {result.files_discovered}")
    click.echo(f"  Processed:    {result.files_processed}")
    click.echo(f"  Skipped:      {result.files_skipped}")
    click.echo(f"  Deduplicated: {result.files_deduplicated}")
    click.echo()


def _show_status(state_db: str) -> None:
    from pathlib import Path

    if not Path(state_db).exists():
        click.echo("No pipeline state found. Run the pipeline first.")
        return

    from src.utils.state_store import StateStore

    state = StateStore(state_db)
    last_run = state.get_last_successful_run()

    if not last_run:
        click.echo("No completed pipeline runs found.")
    else:
        click.echo("\n--- Last Successful Run ---")
        click.echo(f"  Run ID:       {last_run.run_id}")
        click.echo(f"  Mode:         {last_run.mode}")
        click.echo(f"  Started:      {last_run.started_at}")
        click.echo(f"  Completed:    {last_run.completed_at}")
        click.echo(f"  Discovered:   {last_run.files_discovered}")
        click.echo(f"  Processed:    {last_run.files_processed}")
        click.echo(f"  Skipped:      {last_run.files_skipped}")
        click.echo(f"  Deduplicated: {last_run.files_deduplicated}")

    processed = state.get_all_processed()
    skipped = state.get_all_skipped()
    click.echo(f"\n  Total processed emails: {len(processed)}")
    click.echo(f"  Total skipped files:    {len(skipped)}")
    click.echo()

    state.close()


if __name__ == "__main__":
    cli()
