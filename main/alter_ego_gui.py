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
# Config / Themes
# =========================
CONFIG_DIR = APP_DIR
CONFIG_PATH = CONFIG_DIR / "gui_config.json"
LEGACY_CONFIG_PATHS = [
    APP_DIR / "config" / "gui_config.json",
    APP_DIR.parent / "gui_config.json",
    APP_DIR.parent / "config" / "gui_config.json",
]
LEGACY_THEME_DIRS = [APP_DIR.parent / "themes"]


def _resolve_theme_dir() -> Path:
    env_dir = os.getenv("THEME_DIR")
    if env_dir:
        return Path(env_dir)

    candidate = APP_DIR / "themes"
    if candidate.exists():
        return candidate

    for legacy in LEGACY_THEME_DIRS:
        if legacy.exists():
            log.warning(
                "Using legacy theme directory at %s; move themes to %s or set THEME_DIR.",
                legacy,
                candidate,
            )
            return legacy

    return candidate


def _migrate_legacy_config() -> None:
    if CONFIG_PATH.exists():
        return

    for legacy_path in LEGACY_CONFIG_PATHS:
        if not legacy_path.exists():
            continue
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(legacy_path.read_text(encoding="utf-8"), encoding="utf-8")
            log.info("Migrated legacy GUI config from %s to %s", legacy_path, CONFIG_PATH)
            return
        except Exception as exc:
            log.warning("Failed to migrate GUI config from %s: %s", legacy_path, exc)


# Looks for JSON themes under main/themes or THEME_DIR override
THEME_DIR = _resolve_theme_dir()

BUILTIN_THEMES: dict[str, dict] = {
    "dark": {
        "bg": "#1f1f2e",
        "text_bg": "#2e2e3f",
        "text_fg": "#dcdcdc",
        "user_fg": "#85d6ff",
        "alter_fg": "#f5b6ff",
        "entry_bg": "#3c3c50",
        "entry_fg": "#ffffff",
        "font_family": "Consolas",
        "font_size": 11,
    },
    "eden": {
        "bg": "#101820",
        "text_bg": "#0f2740",
        "text_fg": "#e0f7fa",
        "user_fg": "#29b6f6",
        "alter_fg": "#ff80ab",
        "entry_bg": "#1c2b36",
        "entry_fg": "#ffffff",
        "font_family": "Corbel",
        "font_size": 18,
    },
    "light": {
        "bg": "#fafafa",
        "text_bg": "#ffffff",
        "text_fg": "#222222",
        "user_fg": "#0044cc",
        "alter_fg": "#880088",
        "entry_bg": "#f0f0f0",
        "entry_fg": "#000000",
        "font_family": "Segoe UI",
        "font_size": 12,
    },
}


def load_gui_config() -> dict:
    _migrate_legacy_config()
    cfg = {"theme": "eden", "model": None, "prismari_enabled": True}
    if CONFIG_PATH.exists():
        try:
            if isinstance(loaded := json.loads(CONFIG_PATH.read_text(encoding="utf-8")), dict):
                cfg |= loaded
        except Exception as exc:
            log.warning("Could not read %s: %s", CONFIG_PATH, exc)

    if env_theme := os.getenv("ALTER_EGO_THEME"):
        cfg["theme"] = env_theme

    return cfg


def save_gui_config(cfg: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception as exc:
        log.warning("Could not write %s: %s", CONFIG_PATH, exc)


def _coerce_theme_from_tokens(name: str, tokens: dict) -> dict:
    def tok(k, default):
        return tokens.get(k, default)

    bg = tok("background", "#1f1f2e")
    text_bg = tok("panel", tok("background-2", "#2e2e3f"))
    text_fg = tok("foreground", "#dcdcdc")
    entry_bg = tok("input-bg", "#3c3c50")
    entry_fg = tok("input-fg", "#ffffff")
    user_fg = tok("accent", "#85d6ff")
    alter_fg = tok("highlight", "#f5b6ff")
    font_family = tokens.get("font_family", "Consolas")
    try:
        font_size = int(tokens.get("font_size", 11))
    except Exception:
        font_size = 11

    return {
        "bg": bg,
        "text_bg": text_bg,
        "text_fg": text_fg,
        "user_fg": user_fg,
        "alter_fg": alter_fg,
        "entry_bg": entry_bg,
        "entry_fg": entry_fg,
        "font_family": font_family,
        "font_size": font_size,
        "_source": f"tokens:{name}",
    }


def _select_palette_from_collection(data: dict) -> dict | None:
    palettes = data.get("eden_themes")
    if not isinstance(palettes, list) or not palettes:
        return None

    default_name = data.get("default_palette")
    if default_name:
        for palette in palettes:
            if palette.get("name") == default_name:
                return palette

    return palettes[0]


def _extract_tokens_payload(name: str, data: dict) -> tuple[str, dict] | None:
    tokens = data.get("tokens")
    if isinstance(tokens, dict):
        return data.get("name", name), tokens
    return None


def _build_direct_theme(name: str, data: dict) -> dict | None:
    keys = {"bg", "text_bg", "text_fg", "user_fg", "alter_fg", "entry_bg", "entry_fg"}
    if not any(k in data for k in keys):
        return None

    merged = BUILTIN_THEMES["dark"].copy()
    merged.update(data)
    merged.setdefault("font_family", "Consolas")
    merged.setdefault("font_size", 11)
    merged["_source"] = f"direct:{name}"
    return merged


def _normalize_theme_json(name: str, data: dict) -> dict | None:
    if palette := _select_palette_from_collection(data):
        return _coerce_theme_from_tokens(palette.get("name", name), palette.get("tokens", {}))

    if tokens_payload := _extract_tokens_payload(name, data):
        payload_name, tokens = tokens_payload
        return _coerce_theme_from_tokens(payload_name, tokens)

    return _build_direct_theme(name, data)


def load_json_themes(theme_dir: Path) -> dict[str, dict]:
    """Return theme definitions discovered under ``theme_dir``.

    The GUI only activates these palettes when the directory contains
    at least one valid JSON file. When the folder is empty or missing, the
    caller is expected to fall back to :data:`BUILTIN_THEMES`.
    """

    themes: dict[str, dict] = {}
    if not theme_dir.exists():
        return themes
    for p in sorted(theme_dir.glob("*.json")):
        try:
            if norm := _normalize_theme_json(p.stem, json.loads(p.read_text(encoding="utf-8"))):
                themes[p.stem] = norm
        except Exception as exc:
            log.error("Failed to load theme file '%s': %s", p, exc)
    return themes

# =========================
# Model folder utilities
# =========================
def _default_models_dir() -> Path:
    for env in ("GPT4ALL_MODEL_DIR", "GPT4ALL_MODELS_DIR"):
        d = os.getenv(env)
        if d and Path(d).exists():
            return Path(d)
    lad = os.getenv("LOCALAPPDATA")
    if lad:
        p = Path(lad) / "nomic.ai" / "GPT4All"
        if p.exists():
            return p
    p = Path.home() / "AppData" / "Local" / "nomic.ai" / "GPT4All"
    if p.exists():
        return p
    fallback = APP_DIR / "models"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _list_models(models_dir: Path) -> list[str]:
    try:
        return sorted([p.name for p in models_dir.glob("*.gguf")])
    except Exception:
        log.exception("Failed to list models in directory: %s", models_dir)
        return []

# =========================
# TTS engine (threaded)
# =========================
ENABLE_TTS = os.getenv("ENABLE_TTS", "1") != "0"
_tts_q: queue.Queue[str] | None = None
_tts_thread: threading.Thread | None = None


def _start_tts_loop():
    global _tts_q, _tts_thread
    if not (ENABLE_TTS and pyttsx3 is not None):
        return
    _tts_q = queue.Queue()

    def _loop():
        try:
            eng = pyttsx3.init()
            eng.setProperty("rate", 165)
            eng.setProperty("volume", 0.9)
            while True:
                msg = _tts_q.get()
                if msg is None:  # sentinel for shutdown
                    break
                eng.say(msg)
                eng.runAndWait()
        except Exception as e:
            log.warning(f"[tts_warning] {e}")

    _tts_thread = threading.Thread(target=_loop, daemon=True)
    _tts_thread.start()


def _speak(text: str):
    if _tts_q is not None:
        _tts_q.put(text)

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
            self.display_text("[notice] No model selected. Open Models → pick a .gguf to load.\n\n", "alter")
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
                    "[guide] No .gguf files detected yet. Use the README link to download a model "
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
            theme = BUILTIN_THEMES["eden"]
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
