"""Full-screen interactive cache dashboard (ncdu/lazydocker-style) built on Textual.

Launched by `sclean ui`. Requires the optional `textual` dependency: install
with `pip install 'superclean[tui]'`. Import this module lazily — never at
package import time — so plain `sclean` usage never pulls in textual.
"""

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Label

from .core import delete_cache_target, format_size, scan_cache_targets
from .registry import build_registry


class ConfirmScreen(ModalScreen[bool]):
    """Modal yes/no confirmation dialog."""

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "No", show=False),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label(self.message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes (y)", variant="error", id="yes")
                yield Button("No (n)", variant="primary", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class CacheDashboard(App):
    """Interactive dashboard for scanning and cleaning development caches."""

    TITLE = "superclean — cache dashboard"

    CSS = """
    ConfirmScreen { align: center middle; }
    #confirm-dialog {
        width: 64;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    #confirm-message { width: 100%; content-align: center middle; }
    #confirm-buttons { height: auto; align-horizontal: center; }
    #confirm-buttons Button { margin: 1 2 0 2; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "rescan", "Rescan"),
        Binding("space", "toggle_selected", "Select"),
        Binding("a", "toggle_all", "All/None"),
        Binding("x", "clean_selected", "Clean"),
        Binding("c", "clean_selected", "Clean", show=False),
    ]

    def __init__(self, registry=None, dry_run: bool = False) -> None:
        """`registry` defaults to the real cleaner registry; pass a fake
        `CleanerRegistry` (e.g. with a mock cleaner pointed at a tmp dir) in
        tests so nothing real is ever scanned or deleted.
        """
        super().__init__()
        self._cleaner_registry = registry
        self._dry_run = dry_run
        self._targets = []
        self._selected = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="targets-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#targets-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Sel", "Target", "Path", "Size")
        self.action_rescan()

    # ------------------------------------------------------------------ scan

    def action_rescan(self) -> None:
        table = self.query_one("#targets-table", DataTable)
        table.loading = True
        self.sub_title = "scanning..."
        self.run_worker(self._scan, thread=True, exclusive=True, group="scan")

    def _scan(self) -> None:
        registry = (
            self._cleaner_registry
            if self._cleaner_registry is not None
            else build_registry()
        )
        targets = scan_cache_targets(registry)
        self.call_from_thread(self._populate, targets)

    def _populate(self, targets) -> None:
        table = self.query_one("#targets-table", DataTable)
        cursor = table.cursor_row or 0

        self._targets = targets
        valid_paths = {t.path for t in targets}
        self._selected &= valid_paths

        table.clear()
        for target in targets:
            checkbox = Text("[x]") if target.path in self._selected else Text("[ ]")
            table.add_row(
                checkbox,
                Text(target.label),
                Text(target.path),
                Text(format_size(target.size)),
            )
        table.loading = False
        if targets:
            table.move_cursor(row=min(cursor, len(targets) - 1))

        total = sum(t.size for t in targets)
        mode = " [DRY RUN]" if self._dry_run else ""
        self.sub_title = f"{len(targets)} targets, {format_size(total)} total{mode}"

    # ------------------------------------------------------------- selection

    def _highlighted_target(self):
        table = self.query_one("#targets-table", DataTable)
        row = table.cursor_row
        if row is None or not (0 <= row < len(self._targets)):
            return None
        return self._targets[row]

    def action_toggle_selected(self) -> None:
        target = self._highlighted_target()
        if target is None:
            return
        if target.path in self._selected:
            self._selected.discard(target.path)
        else:
            self._selected.add(target.path)
        self._populate(self._targets)

    def action_toggle_all(self) -> None:
        if self._selected:
            self._selected.clear()
        else:
            self._selected = {t.path for t in self._targets}
        self._populate(self._targets)

    # ------------------------------------------------------------- cleaning

    def action_clean_selected(self) -> None:
        selected = [t for t in self._targets if t.path in self._selected]
        if not selected:
            self.notify("No targets selected", severity="warning")
            return

        total = sum(t.size for t in selected)
        if self._dry_run:
            message = (
                f"[DRY RUN] Would delete {len(selected)} target(s), "
                f"freeing {format_size(total)}. Continue?"
            )
        else:
            message = f"Delete {len(selected)} target(s), freeing {format_size(total)}?"

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._start_clean(selected)

        self.push_screen(ConfirmScreen(message), on_confirm)

    def _start_clean(self, targets) -> None:
        self.run_worker(
            lambda: self._clean(targets), thread=True, exclusive=True, group="clean"
        )

    def _clean(self, targets) -> None:
        freed = 0
        for target in targets:
            freed += delete_cache_target(target, dry_run=self._dry_run)
            self._selected.discard(target.path)
        verb = "Would free" if self._dry_run else "Freed"
        self.call_from_thread(
            self.notify, f"{verb} {format_size(freed)}", title="Clean complete"
        )
        self.call_from_thread(self.action_rescan)
