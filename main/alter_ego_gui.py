"""Alter/Ego GUI frontend with modular helpers and first-run guidance."""

from __future__ import annotations

import datetime
import logging
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from alter_shell import AlterShell
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
        cfg_models_dir = self.cfg.get("model_dir")
        if cfg_models_dir:
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

        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state=tk.NORMAL)
        self.text_area.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        entry_frame = tk.Frame(self)
        entry_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        entry_frame.columnconfigure(0, weight=1)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(entry_frame, textvariable=self.entry_var)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", self._on_send)

        send_button = tk.Button(entry_frame, text="Send", command=self._on_send)
        send_button.grid(row=0, column=1, padx=(8, 0))

        self.status_var = tk.StringVar(value="persona: none | model: auto")
        status = tk.Label(self, textvariable=self.status_var, anchor="w")
        status.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        self._build_menu()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        for name in sorted(self.themes):
            theme_menu.add_command(label=name, command=lambda n=name: self._apply_theme(n))
        menu_bar.add_cascade(label="Themes", menu=theme_menu)

        model_menu = tk.Menu(menu_bar, tearoff=0)
        model_menu.add_command(label="Choose model directory…", command=self._pick_model_dir)
        model_menu.add_separator()
        self.model_menu = model_menu
        menu_bar.add_cascade(label="Models", menu=model_menu)

        persona_menu = tk.Menu(menu_bar, tearoff=0)
        persona_menu.add_command(label="Choose persona file…", command=self._pick_persona_file)
        persona_menu.add_command(label="Refresh personas", command=self._refresh_persona_hint)
        menu_bar.add_cascade(label="Personas", menu=persona_menu)

        self.config(menu=menu_bar)
        self._refresh_models_menu()

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
        self.text_area.configure(bg=text_bg, fg=text_fg, font=(font_family, font_size))
        self.entry.configure(bg=entry_bg, fg=entry_fg, font=(font_family, font_size))

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
        self.model_menu.delete(2, tk.END)
        self.models = list_models(self.models_dir)
        if not self.models:
            self.model_menu.add_command(label="No models found", state=tk.DISABLED)
            self.model_menu.add_command(
                label="Open models folder",
                command=lambda: self._open_folder(self.models_dir),
            )
            return

        for name in self.models:
            def _select(n=name):
                self._set_model_selection(n)

            label = f"{name}"
            if name == self.current_model:
                label = f"✓ {name}"
            self.model_menu.add_command(label=label, command=_select)

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
        selected = filedialog.askdirectory(initialdir=self.models_dir)
        if selected:
            self.models_dir = Path(selected)
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
        path = filedialog.askopenfilename(initialdir=persona_root, filetypes=filetypes)
        if path:
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
        self._insert_persona_hint()

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
        self.status_var.set(f"persona: {persona} | model: {model}")

    # ------------------------------------------------------------------
    def _append(self, text: str) -> None:
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

    # ------------------------------------------------------------------
    def _on_send(self, event=None) -> None:
        message = self.entry_var.get().strip()
        if not message:
            return
        self.entry_var.set("")
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
    def _insert_banner(self, label: str, body: str) -> None:
        banner = f"[{label}] {body}\n"
        self._append(banner)

    # ------------------------------------------------------------------
    def _insert_welcome_guidance(self) -> None:
        self._insert_banner(
            "welcome",
            "Thank you for trusting Alter/Ego. The README hosts setup notes if you ever feel lost.",
        )
        self._insert_persona_hint()
        self._insert_model_hint()

    # ------------------------------------------------------------------
    def _persona_files_present(self, root: Path) -> bool:
        for pattern in ("*.chaos", "*.mirror.json"):
            if any(root.glob(pattern)):
                return True
        return False

    # ------------------------------------------------------------------
    def _insert_persona_hint(self) -> None:
        persona_root = get_persona_root()
        if not self._persona_files_present(persona_root):
            self._insert_banner(
                "notice",
                (
                    f"No personas found in {persona_root}. Drop `.chaos` or `.mirror.json` files there, or read the persona guide:\n"
                    "https://github.com/Autumnus-Labs/AlterEgo#persona-simulation"
                ),
            )
        else:
            active = self.fronting.get_active() or "Rhea"
            self._insert_banner("persona", f"Currently fronting {active}. Personas live in {persona_root}.")

    # ------------------------------------------------------------------
    def _insert_model_hint(self) -> None:
        models = list_models(self.models_dir)
        starter = starter_model_path(self.models_dir)
        if not models:
            self._insert_banner(
                "models",
                (
                    f"Drop GGUF files into {self.models_dir} to enable GPT4All. We recommend starting with {STARTER_MODEL}.\n"
                    "Read more: https://github.com/Autumnus-Labs/AlterEgo#starter-model"
                ),
            )
        elif not starter.exists():
            self._insert_banner(
                "models",
                (
                    f"Consider downloading the starter model {STARTER_MODEL} for the best first-run experience.\n"
                    f"Store it at {starter}."
                ),
            )
        else:
            self._insert_banner(
                "models",
                f"Models loaded from {self.models_dir}. Starter model detected: {STARTER_MODEL}.",
            )

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
