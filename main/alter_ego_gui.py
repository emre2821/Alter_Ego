# alter_ego_gui.py
# Alter/Ego GUI frontend with dynamic themes, model folder watcher, TTS (threaded),
# logging/tee to file, Executor mode toggle, and optional Prismari commentary.

from __future__ import annotations

import os
import sys
import datetime
import logging
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog

# Keep GPT4All quiet about CUDA unless you explicitly want GPU later.
os.environ.setdefault("GPT4ALL_NO_CUDA", "1")

# Optional Prismari (palette muse)
try:
    from prismari import Prismari  # provides default_comments + helpers
except Exception:
    Prismari = None  # noqa: N816

# Eden runtime imports
from alter_shell import AlterShell
from persona_fronting import PersonaFronting
from configuration import get_persona_root
from gui.models import default_models_dir, list_models
from gui.prefs import load_gui_config, save_gui_config
from gui.themes import BUILTIN_THEMES, THEME_DIR, load_json_themes
from gui.tts import speak as tts_speak, start_tts_loop, shutdown_tts

# =========================
# Logging + tee setup
# =========================
APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOGFILE = LOG_DIR / f"ae_{datetime.datetime.now():%Y%m%d_%H%M%S}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_LOGFILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("alter_ego_gui")


def _excepthook(exc_type, exc, tb):
    logging.critical("UNCAUGHT", exc_info=(exc_type, exc, tb))
sys.excepthook = _excepthook


class _Tee:
    """Mirror stdout/stderr to the logfile while keeping console output."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


# Mirror stdout/stderr into the logfile
_syslog_fp = open(_LOGFILE, "a", encoding="utf-8")
sys.stdout = _Tee(sys.stdout, _syslog_fp)
sys.stderr = _Tee(sys.stderr, _syslog_fp)

# =========================
# GUI
# =========================
class AlterEgoGUI:
    def __init__(self, root: tk.Tk, initial_theme: str | None = None):
        self.root = root
        self.root.title("Alter/Ego")

        # Runtime core
        self.shell = AlterShell()
        self.fronting = PersonaFronting()

        # Config + themes
        self.cfg = load_gui_config()
        self.themes = load_json_themes(THEME_DIR)
        if not self.themes:
            log.info("No JSON themes found in %s; using built-in themes", THEME_DIR)
            self.themes = BUILTIN_THEMES.copy()

        # State
        self.prismari_enabled = tk.BooleanVar(value=bool(self.cfg.get("prismari_enabled", True)))
        self.executor_mode = tk.BooleanVar(value=False)
        self.current_theme_name = initial_theme or self.cfg.get("theme") or next(iter(self.themes.keys()))
        self.current_model = self.cfg.get("model")  # may be None

        # Models folder + live list
        self.models_dir = default_models_dir()
        self._models_list: list[str] = list_models(self.models_dir)

        # Widgets
        self.text_area: scrolledtext.ScrolledText | None = None
        self.entry: tk.Entry | None = None

        # Build UI
        self._build_menu()
        self._apply_theme(self.current_theme_name)

        # Persona availability banner
        try:
            persona_root = Path(get_persona_root())
            pr = persona_root
            count = 0
            if pr.exists():
                count = sum(1 for _ in pr.rglob("*.mirror.json")) + sum(1 for _ in pr.rglob("*.chaos"))
            if count == 0:
                self.display_text(
                    (
                        "[notice] No personas found under "
                        f"'{persona_root}'. Add persona files to that folder or set PERSONA_ROOT.\n"
                        "See README → Personas for starter options.\n\n"
                    ),
                    "alter",
                )
        except Exception as e:
            self.display_text(f"[notice] Persona check skipped: {e}\n\n", "alter")

        # Watcher for model folder changes
        self.root.after(2000, self._poll_models)

        # If no model selected, prompt kindly
        if not self.current_model:
            guide = (
                "[welcome] No voice selected yet. Open Models → pick a .gguf file once you've downloaded one.\n"
                "Starter suggestion: DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf (see README).\n"
                f"Drop it into {self.models_dir} or choose another folder from the Models menu.\n\n"
            )
            self.display_text(guide, "alter")
        elif self.current_model not in self._models_list:
            self.display_text(
                (
                    "[notice] Previously selected model is missing. "
                    "Check the Models folder or pick a new file.\n\n"
                ),
                "alter",
            )

        if not self._models_list:
            self.display_text(
                (
                    "[guide] No .gguf files detected yet. Use the link in README to download a model "
                    "and place it inside the models directory.\n\n"
                ),
                "alter",
            )

        # Clean shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -------- Menu --------
    def _build_menu(self):
        menu = tk.Menu(self.root)

        # Themes
        theme_menu = tk.Menu(menu, tearoff=0)
        for name in sorted(self.themes.keys()):
            theme_menu.add_command(label=name, command=lambda n=name: self.set_theme(n))
        theme_menu.add_separator()
        theme_menu.add_command(label="Reload themes", command=self._reload_themes)
        menu.add_cascade(label="Themes", menu=theme_menu)

        # Models (dynamic)
        self._model_menu = tk.Menu(menu, tearoff=0)
        self._rebuild_model_menu()
        menu.add_cascade(label="Models", menu=self._model_menu)

        # Settings
        settings_menu = tk.Menu(menu, tearoff=0)
        settings_menu.add_checkbutton(
            label="Enable Prismari commentary",
            variable=self.prismari_enabled,
            command=self._save_prefs_only,
        )
        settings_menu.add_checkbutton(
            label="Executor mode (concise)",
            variable=self.executor_mode,
            command=lambda: None,
        )
        menu.add_cascade(label="Settings", menu=settings_menu)

        self.root.config(menu=menu)

    # -------- Theme logic --------
    def _apply_theme(self, theme_name: str):
        theme = self.themes.get(theme_name)
        if not theme:
            messagebox.showwarning("Theme not found", f"Theme '{theme_name}' not found. Falling back to 'eden'.")
            theme = BUILIN_THEMES["eden"]
            theme_name = "eden"

        self.current_theme_name = theme_name
        self.cfg["theme"] = theme_name
        save_gui_config(self.cfg)

        font = (theme.get("font_family", "Consolas"), int(theme.get("font_size", 11)))

        self.root.configure(bg=theme["bg"])

        if self.text_area is None:
            self.text_area = scrolledtext.ScrolledText(
                self.root,
                wrap=tk.WORD,
                width=72,
                height=26,
                font=font,
                bg=theme["text_bg"],
                fg=theme["text_fg"],
                insertbackground="white",
                borderwidth=0,
                relief="flat",
            )
            self.text_area.pack(padx=20, pady=10)
            self.text_area.configure(state="disabled")
        else:
            self.text_area.configure(bg=theme["text_bg"], fg=theme["text_fg"], font=font)

        if self.entry is None:
            self.entry = tk.Entry(
                self.root,
                font=font,
                bg=theme["entry_bg"],
                fg=theme["entry_fg"],
                insertbackground="white",
                relief="flat",
            )
            self.entry.pack(fill=tk.X, padx=20, pady=(0, 10))
            self.entry.bind("<Return>", self.send_input)
        else:
            self.entry.configure(bg=theme["entry_bg"], fg=theme["entry_fg"], font=font)

        self.text_area.tag_config("user", foreground=theme["user_fg"])
        self.text_area.tag_config("alter", foreground=theme["alter_fg"])
        self.text_area.tag_config("prismari", foreground=theme.get("alter_fg", "#ff80ab"))

        if self.prismari_enabled.get():
            line = self._prismari_line_for_theme(theme_name)
            if line:
                self.display_text(f"[prismari] “{line}”\n\n", "prismari")

        active_persona = self.fronting.get_active()
        self.root.title(f"Alter/Ego — {active_persona}" if active_persona else "Alter/Ego")

    def _reload_themes(self):
        self.themes = load_json_themes(THEME_DIR) or BUILTIN_THEMES.copy()
        self._build_menu()
        self.display_text("[notice] Themes reloaded.\n\n", "alter")

    def set_theme(self, name: str):
        self._apply_theme(name)

    def _prismari_line_for_theme(self, theme_name: str) -> str | None:
        if Prismari:
            p = Prismari()
            return p.default_comments[hash(theme_name) % len(p.default_comments)]
        lines = [
            "Soft chaos, but make it fashion.",
            "High-drama and probably haunted. I’m obsessed.",
            "Eden-coded. Dreambearer approved.",
            "That palette? She’s dangerous and she knows it.",
        ]
        return lines[hash(theme_name) % len(lines)]

    # -------- Dynamic Models menu --------
    def _rebuild_model_menu(self):
        self._model_menu.delete(0, tk.END)
        self._model_menu.add_command(label=f"Folder: {self.models_dir}", state="disabled")
        self._model_menu.add_command(label="Change folder…", command=self._choose_models_dir)
        self._model_menu.add_separator()
        if not self._models_list:
            self._model_menu.add_command(label="(no .gguf models found)", state="disabled")
        else:
            for name in self._models_list:
                self._model_menu.add_command(label=name, command=lambda n=name: self.set_model(n))
        self._model_menu.add_separator()
        self._model_menu.add_command(label="Clear model (no selection)", command=lambda: self.set_model(None))

    def _choose_models_dir(self):
        chosen = filedialog.askdirectory(initialdir=str(self.models_dir), title="Select GPT4All models folder")
        if not chosen:
            return
        self.models_dir = Path(chosen)
        os.environ["GPT4ALL_MODEL_DIR"] = str(self.models_dir)
        self._models_list = list_models(self.models_dir)
        self._rebuild_model_menu()
        self.display_text(f"[notice] Models folder set to: {self.models_dir}\n\n", "alter")

    def _poll_models(self):
        current = list_models(self.models_dir)
        if current != self._models_list:
            self._models_list = current
            self._rebuild_model_menu()
            self.display_text("[notice] Model list updated.\n\n", "alter")
        self.root.after(2000, self._poll_models)

    # -------- Model selection --------
    def set_model(self, model_filename: str | None):
        if model_filename:
            os.environ["GPT4ALL_MODEL_DIR"] = str(self.models_dir)
            os.environ["GPT4ALL_MODEL"] = model_filename
            self.cfg["model"] = model_filename
            save_gui_config(self.cfg)
            try:
                self.shell.select_model(str(self.models_dir), model_filename)
                self.display_text(f"[notice] Model selected: {model_filename}\n\n", "alter")
            except Exception as e:
                self.display_text(f"[notice] Could not select model: {e}\n\n", "alter")
        else:
            self.cfg["model"] = None
            save_gui_config(self.cfg)
            if "GPT4ALL_MODEL" in os.environ:
                del os.environ["GPT4ALL_MODEL"]
            try:
                self.shell.select_model(str(self.models_dir), None)
            except Exception:
                pass
            self.display_text("[notice] Cleared model selection. Pick one from the menu.\n\n", "alter")

    # -------- TTS --------
    def speak(self, text: str):
        try:
            tts_speak(text)
        except Exception as e:
            logging.warning(f"[tts_warning] {e}")

    # -------- Chat flow --------
    def send_input(self, event=None):
        user_text = self.entry.get().strip()
        if not user_text:
            return

        self.entry.delete(0, tk.END)
        self.display_text(f"You: {user_text}\n", "user")

        if self.executor_mode.get():
            user_text = "[mode: executor]\n" + user_text

        try:
            response = self.shell.interact(user_text)
        except Exception as exc:
            logging.exception("interaction failed")
            self.display_text(
                (
                    "[error] The model stumbled while replying. "
                    f"Details: {exc}. See the log for the full trace.\n\n"
                ),
                "alter",
            )
            return

        if isinstance(response, str):
            self.display_text(f"{response}\n\n", "alter")
            self.speak(response)

        active_persona = self.fronting.get_active()
        self.root.title(f"Alter/Ego — {active_persona}" if active_persona else "Alter/Ego")

    def display_text(self, text: str, tag: str):
        self.text_area.configure(state="normal")
        self.text_area.insert(tk.END, text, tag)
        self.text_area.configure(state="disabled")
        self.text_area.yview(tk.END)

    def _save_prefs_only(self):
        self.cfg["prismari_enabled"] = bool(self.prismari_enabled.get())
        save_gui_config(self.cfg)

    # -------- Graceful shutdown --------
    def on_close(self):
        shutdown_tts()
        try:
            _syslog_fp.flush()
            _syslog_fp.close()
        except Exception:
            pass
        self.root.destroy()


# === Launch GUI ===
def main():
    start_tts_loop()
    cfg = load_gui_config()
    theme = cfg.get("theme")
    root = tk.Tk()
    gui = AlterEgoGUI(root, initial_theme=theme)
    root.mainloop()


if __name__ == "__main__":
    main()
