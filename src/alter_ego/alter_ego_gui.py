"""Alter/Ego GUI frontend with modular helpers and first-run guidance."""

from __future__ import annotations

import datetime
import logging
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from alter_shell import AlterShell
if __package__:
    from .configuration import get_persona_root
else:
    from configuration import get_persona_root
from gui.models import (
    STARTER_MODEL,
    current_selection,
    list_models,
    resolve_models_dir,
    starter_model_path,
)
from gui.prefs import load_gui_config, save_gui_config
from gui.themes import available_themes, discover_theme_dir
from gui.tts import shutdown as shutdown_tts, speak as tts_speak, start as start_tts
from gui.ui_helpers import (
    BannerManager,
    ConversationPane,
    EntryPanel,
    MenuBuilder,
    StatusBar,
)
from persona_fronting import PersonaFronting

os.environ.setdefault("GPT4ALL_NO_CUDA", "1")

APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"ae_{datetime.datetime.now():%Y%m%d_%H%M%S}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("alter_ego_gui")


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            try:
                stream.write(data)
            except Exception:
                pass

    def flush(self):
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:
                pass


def _excepthook(exc_type, exc, tb):
    logging.critical("UNCAUGHT", exc_info=(exc_type, exc, tb))


sys.excepthook = _excepthook
_syslog_fp = open(LOG_FILE, "a", encoding="utf-8")
sys.stdout = _Tee(sys.stdout, _syslog_fp)
sys.stderr = _Tee(sys.stderr, _syslog_fp)


class AlterEgoGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Alter/Ego")

        self.fronting = PersonaFronting()
        self.shell = AlterShell()
        start_tts()

        self.cfg = load_gui_config()
        self.theme_dir = discover_theme_dir()
        self.themes = available_themes(self.theme_dir)

        self.models_dir = resolve_models_dir()
        if cfg_models_dir := self.cfg.get("model_dir"):
            candidate = Path(cfg_models_dir)
            if candidate.exists():
                self.models_dir = candidate
        self.models = list_models(self.models_dir)
        self.current_model = None

        self._build_ui()
        self._apply_theme(self.cfg.get("theme", "eden"))
        self._restore_model_selection()
        self._insert_welcome_guidance()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.geometry("960x720")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)

        self.conversation_pane = ConversationPane(self)
        self.conversation_pane.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.entry_panel = EntryPanel(self)
        self.entry_panel.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.entry_panel.bind_send(self._on_send)

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        self.menus = MenuBuilder(
            self,
            themes=self.themes,
            on_theme_selected=self._apply_theme,
            on_choose_model_directory=self._pick_model_dir,
            on_choose_persona_file=self._pick_persona_file,
            on_refresh_personas=self._refresh_persona_hint,
        )
        self.banner_manager = BannerManager(
            self.conversation_pane,
            persona_root_provider=get_persona_root,
            fronting_active=self.fronting.get_active,
            models_dir_provider=lambda: self.models_dir,
            list_models=list_models,
            starter_model_path=starter_model_path,
            starter_model_name=STARTER_MODEL,
        )
        self.entry_panel.focus_entry()

        self._build_menu()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        for name in sorted(self.themes):
            theme_menu.add_command(label=name, command=lambda n=name: self._apply_theme(n))
        menu_bar.add_cascade(label="Themes", menu=theme_menu)

        self.model_menu_label = tk.StringVar()
        self._update_model_menu_label()
        model_menu = tk.Menu(menu_bar, tearoff=0)
        self.model_menu = model_menu
        menu_bar.add_cascade(labelvariable=self.model_menu_label, menu=model_menu)

        persona_menu = tk.Menu(menu_bar, tearoff=0)
        persona_menu.add_command(label="Choose persona file…", command=self._pick_persona_file)
        persona_menu.add_command(label="Refresh personas", command=self._refresh_persona_hint)
        menu_bar.add_cascade(label="Personas", menu=persona_menu)

        self.config(menu=menu_bar)
        self._refresh_models_menu()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    def _apply_theme(self, theme_name: str) -> None:
        theme = self.themes.get(theme_name)
        if theme is None:
            theme = self.themes.get("eden", next(iter(self.themes.values())))
        self.cfg["theme"] = theme_name
        save_gui_config(self.cfg)

        bg = theme["bg"]
        text_bg = theme["text_bg"]
        text_fg = theme["text_fg"]
        entry_bg = theme.get("entry_bg", text_bg)
        entry_fg = theme.get("entry_fg", text_fg)
        font_family = theme.get("font_family", "Segoe UI")
        font_size = theme.get("font_size", 12)

        self.configure(bg=bg)
        font = (font_family, font_size)
        self.conversation_pane.apply_theme(background=text_bg, foreground=text_fg, font=font)
        self.entry_panel.apply_theme(background=entry_bg, foreground=entry_fg, font=font)
        self.status_bar.apply_theme(background=bg, foreground=text_fg, font=font)

    # ------------------------------------------------------------------
    def _restore_model_selection(self) -> None:
        models_dir, selected = current_selection(self.models_dir)
        if selected:
            self.models_dir = models_dir
            self.current_model = selected
            self.shell.select_model(str(self.models_dir), self.current_model)
        elif model := self.cfg.get("model"):
            candidate = self.models_dir / model
            if candidate.exists():
                self.current_model = model
                self.shell.select_model(str(self.models_dir), self.current_model)
        self._refresh_models_menu()
        self._update_status()

    # ------------------------------------------------------------------
    def _refresh_models_menu(self) -> None:
        self.models = list_models(self.models_dir)
        self.menus.models.refresh(
            models_dir=self.models_dir,
            models=self.models,
            current_model=self.current_model,
            on_select_model=self._set_model_selection,
            on_open_folder=lambda: self._open_folder(self.models_dir),
        )
        self.model_menu.delete(0, tk.END)
        self.model_menu.add_command(label="Choose model directory…", command=self._pick_model_dir)
        self.model_menu.add_separator()

        self.models = list_models(self.models_dir)
        if not self.models:
            self.model_menu.add_command(label="No models found", state=tk.DISABLED)
        else:
            for name in self.models:
                def _select(n=name):
                    self._set_model_selection(n)

                label = f"{name}"
                if name == self.current_model:
                    label = f"✓ {name}"
                self.model_menu.add_command(label=label, command=_select)

        self.model_menu.add_separator()
        if self.models_dir:
            self.model_menu.add_command(
                label="Open models folder",
                command=lambda: self._open_folder(self.models_dir),
            )
        else:
            self.model_menu.add_command(label="Open models folder", state=tk.DISABLED)
        self._update_model_menu_label()

    # ------------------------------------------------------------------
    def _update_model_menu_label(self) -> None:
        if not hasattr(self, "model_menu_label"):
            return

        if self.models_dir:
            dir_name = Path(self.models_dir).name or str(self.models_dir)
            self.model_menu_label.set(f"Models ({dir_name})")
        else:
            self.model_menu_label.set("Models (no directory chosen)")

    # ------------------------------------------------------------------
    def _set_model_selection(self, model_name: str) -> None:
        self.shell.select_model(str(self.models_dir), model_name)
        self.current_model = model_name
        self.cfg["model"] = model_name
        save_gui_config(self.cfg)
        self._refresh_models_menu()
        self._update_status()

    # ------------------------------------------------------------------
    def _pick_model_dir(self) -> None:
        if selected := filedialog.askdirectory(initialdir=self.models_dir):
            self.models_dir = Path(selected)
            self.menus.models.update_label(self.models_dir)
            self.shell.select_model(str(self.models_dir), self.current_model)
            self.cfg["model_dir"] = str(self.models_dir)
            save_gui_config(self.cfg)
            self._refresh_models_menu()
            self._update_status()

    # ------------------------------------------------------------------
    def _pick_persona_file(self) -> None:
        persona_root = get_persona_root()
        filetypes = [
            ("Persona files", ("*.chaos", "*.mirror.json")),
            ("All files", "*.*"),
        ]
        if path := filedialog.askopenfilename(initialdir=persona_root, filetypes=filetypes):
            try:
                selected = Path(path)
                persona_name = selected.stem
                self.fronting.front(persona_name)
                self._append(f"[persona] Fronting {persona_name}\n")
            except Exception as exc:
                messagebox.showerror("Persona error", str(exc))
        self._update_status()

    # ------------------------------------------------------------------
    def _refresh_persona_hint(self) -> None:
        self.banner_manager.insert_persona_hint()

    # ------------------------------------------------------------------
    def _open_folder(self, path: Path) -> None:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

    # ------------------------------------------------------------------
    def _update_status(self) -> None:
        persona = self.fronting.get_active() or "none"
        model = self.current_model or "auto"
        self.status_bar.update(persona, model)

    # ------------------------------------------------------------------
    def _append(self, text: str) -> None:
        if not hasattr(self, "conversation_pane"):
            raise RuntimeError("Conversation pane is not initialized")
        self.conversation_pane.append(text)

    # ------------------------------------------------------------------
    def _on_send(self, event=None) -> None:
        message = self.entry_panel.get_message()
        if not message:
            return
        self.entry_panel.clear()
        self._append(f"You: {message}\n")

        try:
            response = self.shell.interact(message)
        except Exception as exc:
            logging.exception("shell.interact failed")
            self._append(
                "[error] Something went wrong while talking to the runtime.\n"
            )
            self._append(f"{exc}\n")
            self._append("Check the logs folder for full tracebacks.\n\n")
            return

        self._append(f"Alter/Ego: {response}\n\n")
        tts_speak(response)

    # ------------------------------------------------------------------
    def _insert_welcome_guidance(self) -> None:
        self.banner_manager.insert_welcome()


    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        shutdown_tts()
        save_gui_config(self.cfg)
        self.destroy()


def main() -> None:  # pragma: no cover - GUI entry point
    app = AlterEgoGUI()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover - GUI entry point
    main()
