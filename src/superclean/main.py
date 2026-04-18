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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Preview changes without deleting any files.",
    ),
):
    """
    SuperClean (sclean) - Reclaim your disk space.
    """
    ctx.obj = {"dry_run": dry_run}
    if ctx.invoked_subcommand is None:
        console.print("[bold blue]SuperClean (sclean)[/bold blue]")
        if dry_run:
            console.print("[bold yellow][DRY RUN MODE][/bold yellow]")
        console.print("Use `sclean --help` for available commands.\n")
        list_cleaners(ctx)


@app.command()
def list_cleaners(ctx: typer.Context):
    """List all available cleaners and potential space savings."""
    registry = get_registry()
    dry_run = ctx.obj.get("dry_run", False)
    title = "Available Cleaners"
    if dry_run:
        title += " [yellow](Dry Run Mode)[/yellow]"

    table = Table(title=title)
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
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clean all detected application caches."""
    registry = get_registry()
    dry_run = ctx.obj.get("dry_run", False)

    if not force and not dry_run:
        confirm = typer.confirm("Are you sure you want to clean all caches?")
        if not confirm:
            raise typer.Abort()

    if dry_run:
        console.print("[bold yellow][DRY RUN][/bold yellow] Previewing clean up...")

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
def python(ctx: typer.Context):
    """Clean Python caches."""
    _clean_specific(ctx, "python")


@app.command()
def node(ctx: typer.Context):
    """Clean Node.js caches."""
    _clean_specific(ctx, "node")


@app.command()
def docker(ctx: typer.Context):
    """Clean Docker resources."""
    _clean_specific(ctx, "docker")


@app.command()
def nix(ctx: typer.Context):
    """Clean Nix garbage."""
    _clean_specific(ctx, "nix")


@app.command()
def system(ctx: typer.Context):
    """Clean system temp files."""
    _clean_specific(ctx, "system")


def _clean_specific(ctx: typer.Context, name: str):
    registry = get_registry()
    dry_run = ctx.obj.get("dry_run", False)
    cleaner = registry.get_by_name(name)
    if not cleaner:
        console.print(f"[bold red]Error:[/bold red] Cleaner '{name}' not found.")
        return

    if dry_run:
        console.print(
            f"[bold yellow][DRY RUN][/bold yellow] Previewing clean for [bold cyan]{cleaner.name}[/bold cyan]..."
        )
    else:
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
