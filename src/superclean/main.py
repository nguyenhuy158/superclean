import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
import os

from .core import CleanerRegistry
from .cleaners.python_node import PythonCleaner, NodeCleaner
from .cleaners.docker_nix import DockerCleaner, NixCleaner
from .cleaners.system import SystemCleaner
from . import __version__

app = typer.Typer(help="Universal CLI tool to clean development caches.")
console = Console()


def get_registry():
    registry = CleanerRegistry()
    registry.register(PythonCleaner())
    registry.register(NodeCleaner())
    registry.register(DockerCleaner())
    registry.register(NixCleaner())
    registry.register(SystemCleaner())
    return registry


def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def version_callback(value: bool):
    if value:
        console.print(f"SuperClean version: [bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
):
    """
    SuperClean (sclean) - Reclaim your disk space.
    """
    if ctx.invoked_subcommand is None:
        console.print("[bold blue]SuperClean (sclean)[/bold blue]")
        console.print("Use `sclean --help` for available commands.\n")
        list_cleaners()


@app.command()
def list_cleaners():
    """List all available cleaners and potential space savings."""
    registry = get_registry()
    table = Table(title="Available Cleaners")
    table.add_column("App", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Potential Savings", justify="right", style="magenta")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Calculating space...", total=len(registry.get_all()))
        for cleaner in registry.get_all():
            space = cleaner.check_space()
            table.add_row(cleaner.name, cleaner.description, format_size(space))
            progress.advance(task)

    console.print(table)


@app.command()
def all(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clean all detected application caches."""
    registry = get_registry()
    if not force and not dry_run:
        confirm = typer.confirm("Are you sure you want to clean all caches?")
        if not confirm:
            raise typer.Abort()

    total_reclaimed = 0
    for cleaner in registry.get_all():
        console.print(f"Cleaning [bold cyan]{cleaner.name}[/bold cyan]...")
        result = cleaner.clean(dry_run=dry_run)
        if result.success:
            total_reclaimed += result.space_reclaimed
            if result.message:
                console.print(f"  [dim]{result.message}[/dim]")
        else:
            console.print(f"  [bold red]Error:[/bold red] {result.message}")

    if dry_run:
        console.print(
            f"\n[bold yellow]Dry run complete.[/bold yellow] Estimated savings: [bold green]{format_size(total_reclaimed)}[/bold green]"
        )
    else:
        console.print(
            f"\n[bold green]Success![/bold green] Total reclaimed: [bold green]{format_size(total_reclaimed)}[/bold green]"
        )


@app.command()
def python(dry_run: bool = False):
    """Clean Python caches."""
    _clean_specific("python", dry_run)


@app.command()
def node(dry_run: bool = False):
    """Clean Node.js caches."""
    _clean_specific("node", dry_run)


@app.command()
def docker(dry_run: bool = False):
    """Clean Docker resources."""
    _clean_specific("docker", dry_run)


@app.command()
def nix(dry_run: bool = False):
    """Clean Nix garbage."""
    _clean_specific("nix", dry_run)


@app.command()
def system(dry_run: bool = False):
    """Clean system temp files."""
    _clean_specific("system", dry_run)


def _clean_specific(name: str, dry_run: bool):
    registry = get_registry()
    cleaner = registry.get_by_name(name)
    if not cleaner:
        console.print(f"[bold red]Error:[/bold red] Cleaner '{name}' not found.")
        return

    console.print(f"Cleaning [bold cyan]{cleaner.name}[/bold cyan]...")
    result = cleaner.clean(dry_run=dry_run)
    if result.success:
        msg = (
            f"Reclaimed {format_size(result.space_reclaimed)}"
            if not dry_run
            else "Preview complete"
        )
        console.print(f"[bold green]Done![/bold green] {msg}")
        if result.message:
            console.print(f"  [dim]{result.message}[/dim]")
    else:
        console.print(f"[bold red]Failed:[/bold red] {result.message}")


if __name__ == "__main__":
    app()
