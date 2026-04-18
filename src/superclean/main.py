import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
import os
import shutil
import platform
import psutil

from .core import CleanerRegistry
from .cleaners.python_node import PythonCleaner, NodeCleaner
from .cleaners.docker_nix import DockerCleaner, NixCleaner
from .cleaners.system import SystemCleaner
from .cleaners.dev_tools import BrewCleaner, XcodeCleaner, CargoCleaner, CondaCleaner
from .cleaners.utilities import LazyGitCleaner, LazyDockerCleaner
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
    registry.register(BrewCleaner())
    registry.register(XcodeCleaner())
    registry.register(CargoCleaner())
    registry.register(CondaCleaner())
    registry.register(LazyGitCleaner())
    registry.register(LazyDockerCleaner())
    return registry


def get_useful_tools():
    """List of tools to check for installation and version."""
    return [
        ("rg", "ripgrep"),
        ("uv", "uv"),
        ("lazygit", "lazygit"),
        ("lazydocker", "lazydocker"),
        ("fzf", "fzf"),
        ("gh", "GitHub CLI"),
        ("jq", "jq"),
        ("fd", "fd"),
        ("bat", "bat"),
        ("tldr", "tldr"),
    ]


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
def status(ctx: typer.Context):
    """Show a high-level dashboard of system health and potential savings."""
    registry = get_registry()
    category_savings = {}
    total_savings = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Analyzing system health...", total=len(registry.get_all()))
        for cleaner in registry.get_all():
            space = cleaner.check_space()
            cat = cleaner.category
            category_savings[cat] = category_savings.get(cat, 0) + space
            total_savings += space
            progress.advance(task)

    # Hero Panel
    console.print(
        Panel(
            f"[bold green]{format_size(total_savings)}[/bold green]",
            title="Total Potential Savings",
            subtitle="Run `sclean all` to reclaim",
            style="cyan",
        )
    )

    # Category Panels
    panels = []
    for cat, space in category_savings.items():
        color = "green" if space > 0 else "dim"
        panels.append(
            Panel(
                f"[bold {color}]{format_size(space)}[/bold {color}]",
                title=cat,
                border_style="blue",
            )
        )
    
    console.print(Columns(panels))

    # System Resources Panel
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        def get_bar(pct):
            filled = int(pct / 10)
            return f"[{'#' * filled}{' ' * (10 - filled)}] {pct}%"

        res_table = Table.grid(expand=True)
        res_table.add_column(style="cyan")
        res_table.add_column(justify="right")

        res_table.add_row("CPU Usage", get_bar(cpu_usage))
        res_table.add_row("RAM Usage", get_bar(mem.percent))
        res_table.add_row("Disk Usage", get_bar(disk.percent))

        # Tool Health check
        useful_tools = get_useful_tools()
        installed_count = sum(1 for cmd, name in useful_tools if shutil.which(cmd))
        res_table.add_row("Toolbox", f"[bold green]{installed_count}/{len(useful_tools)}[/bold green] tools installed")

        console.print(Panel(res_table, title="System Resources & Tools", border_style="magenta"))
    except Exception:
        pass

    # System Info Footer
    sys_info = f"OS: [cyan]{platform.system()} {platform.release()}[/cyan] | SuperClean: [cyan]{__version__}[/cyan]"
    console.print(f"\n[dim]{sys_info}[/dim]")


@app.command()
def check():
    """Check if useful developer tools are installed and their versions."""
    table = Table(title="Developer Tools Health Check")
    table.add_column("Status", justify="center")
    table.add_column("Tool", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version", style="magenta")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        tools = get_useful_tools()
        task = progress.add_task("Checking tools...", total=len(tools))
        
        for cmd, name in tools:
            path = shutil.which(cmd)
            status = "[bold green]✅[/bold green]" if path else "[bold red]❌[/bold red]"
            version = "N/A"
            
            if path:
                # Try to get version
                try:
                    # Most tools support --version
                    v_cmd = [cmd, "--version"]
                    # Special cases
                    if cmd == "uv":
                        v_cmd = ["uv", "--version"]
                    
                    import subprocess
                    proc = subprocess.run(v_cmd, capture_output=True, text=True, timeout=1)
                    if proc.returncode == 0:
                        # Extract first line or part of it
                        version = proc.stdout.split('\n')[0].strip()
                        # Shorten if too long
                        if len(version) > 40:
                            version = version[:37] + "..."
                except Exception:
                    version = "Found"

            table.add_row(status, cmd, name, version)
            progress.advance(task)

    console.print(table)


@app.command()
def info():
    """Show detailed system information."""
    table = Table(title="System Information", show_header=False, box=None)
    table.add_column("Property", style="bold cyan")
    table.add_column("Value")

    # OS Info
    table.add_row("OS", f"{platform.system()} {platform.release()}")
    table.add_row("Machine", platform.machine())
    table.add_row("Processor", platform.processor())
    table.add_row("Python", platform.python_version())

    # CPU Info
    cpu_count = psutil.cpu_count(logical=False)
    logical_cpu = psutil.cpu_count(logical=True)
    table.add_row("CPU Cores", f"{cpu_count} physical, {logical_cpu} logical")
    table.add_row("CPU Usage", f"{psutil.cpu_percent(interval=0.1)}%")

    # Memory Info
    mem = psutil.virtual_memory()
    used_mem = mem.total - mem.available
    table.add_row("Memory Total", format_size(mem.total))
    table.add_row("Memory Used", f"{format_size(used_mem)} ({mem.percent}%)")
    table.add_row("Memory Free", format_size(mem.available))

    # Disk Info
    disk = psutil.disk_usage('/')
    table.add_row("Disk Total", format_size(disk.total))
    table.add_row("Disk Used", f"{format_size(disk.used)} ({disk.percent}%)")
    table.add_row("Disk Free", format_size(disk.free))

    console.print(Panel(table, expand=False, border_style="cyan"))


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
def cron(
    ctx: typer.Context,
    install: bool = typer.Option(False, "--install", help="Install weekly cron job"),
    uninstall: bool = typer.Option(False, "--uninstall", help="Remove sclean cron job"),
):
    """Manage weekly maintenance automation (via crontab)."""
    import sys
    import subprocess

    # Try to find the absolute path of sclean
    # If installed via pip, it should be in the path.
    # We use 'which' to find it, or fallback to sys.argv[0]
    sclean_path = shutil.which("sclean")
    if not sclean_path:
        sclean_path = os.path.abspath(sys.argv[0])

    cron_cmd = f"0 0 * * 0 {sclean_path} all --force > /dev/null 2>&1"
    
    # Get current crontab
    try:
        current_cron = subprocess.check_output(["crontab", "-l"], text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        current_cron = ""

    if uninstall:
        new_cron = "\n".join([line for line in current_cron.splitlines() if "sclean" not in line and "superclean" not in line])
        process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        console.print("[bold green]Success![/bold green] sclean cron job removed.")
        return

    if install:
        if "sclean" in current_cron or "superclean" in current_cron:
            console.print("[yellow]sclean cron job is already installed.[/yellow]")
            return
        
        new_cron = current_cron.strip() + "\n" + cron_cmd + "\n"
        process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        console.print("[bold green]Success![/bold green] Weekly cleanup scheduled (Sundays at midnight).")
        return

    # Default: view
    sclean_jobs = [line for line in current_cron.splitlines() if "sclean" in line or "superclean" in line]
    if sclean_jobs:
        console.print("[bold blue]Current sclean cron jobs:[/bold blue]")
        for job in sclean_jobs:
            console.print(f"  {job}")
    else:
        console.print("[yellow]No sclean cron jobs found.[/yellow]\nUse `sclean cron --install` to set up weekly cleanup.")


@app.command()
def projects(
    ctx: typer.Context,
    path: str = typer.Argument(".", help="Directory to scan"),
    delete: bool = typer.Option(False, "--delete", "-X", help="Delete found folders"),
    recursive: bool = typer.Option(True, help="Scan recursively"),
):
    """Scan for local project development folders (node_modules, venv, etc.) and optionally delete them."""
    dry_run = ctx.obj.get("dry_run", False)
    target_names = {
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        "target",
        "build",
        "dist",
        ".next",
        ".svelte-kit",
        "bin",
        "obj",
    }
    found_folders = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(f"Scanning {path}...", total=None)

        abs_path = os.path.abspath(path)
        for root, dirs, files in os.walk(abs_path):
            # Check if current directory itself is a target
            # However, usually we look for targets inside projects.
            # If we find a target, we don't need to look inside it.
            i = 0
            while i < len(dirs):
                d = dirs[i]
                if d in target_names:
                    full_path = os.path.join(root, d)
                    found_folders.append(full_path)
                    # Don't recurse into found target folders
                    dirs.pop(i)
                else:
                    i += 1
            if not recursive:
                break
            progress.advance(task)

    if not found_folders:
        console.print("[yellow]No project development folders found.[/yellow]")
        return

    table = Table(title=f"Found Project Folders in {path}")
    table.add_column("Path", style="cyan")
    table.add_column("Size", justify="right", style="magenta")

    total_size = 0
    # We need a dummy cleaner to use get_dir_size or just use a helper
    from .core import BaseCleaner, CleanResult

    class SizeHelper(BaseCleaner):
        @property
        def name(self):
            return ""

        @property
        def category(self):
            return ""

        @property
        def description(self):
            return ""

        def check_space(self):
            return 0

        def clean(self, dry_run=False):
            return CleanResult("", 0, True)

    helper = SizeHelper()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Calculating sizes...", total=len(found_folders))
        for p in found_folders:
            size = helper.get_dir_size(p)
            total_size += size
            table.add_row(p, format_size(size))
            progress.advance(task)

    console.print(table)
    console.print(
        f"\nTotal potential savings: [bold green]{format_size(total_size)}[/bold green]"
    )

    if delete:
        if dry_run:
            console.print(
                "\n[bold yellow][DRY RUN][/bold yellow] Would delete all found folders."
            )
            return

        confirm = typer.confirm("\nAre you sure you want to delete all these folders?")
        if not confirm:
            raise typer.Abort()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Deleting...", total=len(found_folders))
            for p in found_folders:
                import shutil

                shutil.rmtree(p, ignore_errors=True)
                progress.advance(task)

        console.print("\n[bold green]Success![/bold green] All folders deleted.")


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


@app.command()
def brew(ctx: typer.Context):
    """Clean Homebrew versions."""
    _clean_specific(ctx, "brew")


@app.command()
def xcode(ctx: typer.Context):
    """Clean Xcode caches."""
    _clean_specific(ctx, "xcode")


@app.command()
def cargo(ctx: typer.Context):
    """Clean Cargo caches."""
    _clean_specific(ctx, "cargo")


@app.command()
def conda(ctx: typer.Context):
    """Clean Conda caches."""
    _clean_specific(ctx, "conda")


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
