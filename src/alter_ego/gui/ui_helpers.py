"""Reusable GUI helpers for Alter/Ego widgets and menus."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, Sequence

import tkinter as tk
from tkinter import scrolledtext


class ConversationPane:
    """Scrolled text widget that keeps history read-only."""

    def __init__(self, master: tk.Misc) -> None:
        self._widget = scrolledtext.ScrolledText(master, wrap=tk.WORD, state=tk.DISABLED)

    @property
    def widget(self) -> scrolledtext.ScrolledText:
        return self._widget

    def grid(self, **kwargs) -> None:
        self._widget.grid(**kwargs)

    def append(self, text: str) -> None:
        self._widget.configure(state=tk.NORMAL)
        self._widget.insert(tk.END, text)
        self._widget.see(tk.END)
        self._widget.configure(state=tk.DISABLED)

    def apply_theme(self, *, background: str, foreground: str, font: Sequence[object]) -> None:
        self._widget.configure(bg=background, fg=foreground, font=font)


class EntryPanel(tk.Frame):
    """Message entry widget paired with a Send button."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.columnconfigure(0, weight=1)
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self,
            textvariable=self.entry_var,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self.entry.grid(row=0, column=0, sticky="ew")

        self.send_button = tk.Button(self, text="Send")
        self.send_button.grid(row=0, column=1, padx=(8, 0))

    def bind_send(self, callback: Callable[[], None]) -> None:
        def _on_return(event: tk.Event) -> str:
            callback()
            return "break"

        self.entry.bind("<Return>", _on_return)
        self.send_button.configure(command=callback)

    def get_message(self) -> str:
        return self.entry_var.get().strip()

    def clear(self) -> None:
        self.entry_var.set("")

    def focus_entry(self) -> None:
        self.entry.focus_set()

    def apply_theme(self, *, background: str, foreground: str, font: Sequence[object]) -> None:
        self.entry.configure(bg=background, fg=foreground, font=font, insertbackground=foreground)


class StatusBar:
    """Status label tracking the active persona and model."""

    def __init__(self, master: tk.Misc) -> None:
        self._var = tk.StringVar(value="persona: none | model: auto")
        self._label = tk.Label(master, textvariable=self._var, anchor="w")

    def grid(self, **kwargs) -> None:
        self._label.grid(**kwargs)

    def update(self, persona: str, model: str) -> None:
        self._var.set(f"persona: {persona} | model: {model}")

    def apply_theme(self, *, background: str, foreground: str, font: Sequence[object]) -> None:
        self._label.configure(bg=background, fg=foreground, font=font)


class ModelMenuController:
    """Controller for the dynamic Models menu."""

    def __init__(self, menu_bar: tk.Menu, on_choose_directory: Callable[[], None]) -> None:
        self._on_choose_directory = on_choose_directory
        self._label_var = tk.StringVar(value="Models (no directory chosen)")
        self.menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(labelvariable=self._label_var, menu=self.menu)

    def refresh(
        self,
        *,
        models_dir: Path | None,
        models: Iterable[str],
        current_model: str | None,
        on_select_model: Callable[[str], None],
        on_open_folder: Callable[[], None],
    ) -> None:
        self.menu.delete(0, tk.END)
        self.menu.add_command(label="Choose model directory…", command=self._on_choose_directory)
        self.menu.add_separator()

        added_model = False
        for name in models:
            label = f"✓ {name}" if name == current_model else name
            self.menu.add_command(label=label, command=lambda n=name: on_select_model(n))
            added_model = True

        if not added_model:
            self.menu.add_command(label="No models found", state=tk.DISABLED)

        self.menu.add_separator()
        self.menu.add_command(label="Open models folder", command=on_open_folder)
        self.update_label(models_dir)

    def update_label(self, models_dir: Path | None) -> None:
        if models_dir:
            label = models_dir.name or str(models_dir)
            self._label_var.set(f"Models ({label})")
        else:
            self._label_var.set("Models (no directory chosen)")


class MenuBuilder:
    """Constructs the top-level menus for the Alter/Ego GUI."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        themes: Iterable[str],
        on_theme_selected: Callable[[str], None],
        on_choose_model_directory: Callable[[], None],
        on_choose_persona_file: Callable[[], None],
        on_refresh_personas: Callable[[], None],
    ) -> None:
        menu_bar = tk.Menu(master)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        for name in sorted(themes):
            theme_menu.add_command(label=name, command=lambda n=name: on_theme_selected(n))
        menu_bar.add_cascade(label="Themes", menu=theme_menu)

        self.models = ModelMenuController(menu_bar, on_choose_model_directory)

        persona_menu = tk.Menu(menu_bar, tearoff=0)
        persona_menu.add_command(label="Choose persona file…", command=on_choose_persona_file)
        persona_menu.add_command(label="Refresh personas", command=on_refresh_personas)
        menu_bar.add_cascade(label="Personas", menu=persona_menu)

        master.config(menu=menu_bar)
        self.menu_bar = menu_bar


class BannerManager:
    """Helper for inserting informative banners into the conversation pane."""

    def __init__(
        self,
        conversation: ConversationPane,
        *,
        persona_root_provider: Callable[[], Path],
        fronting_active: Callable[[], str | None],
        models_dir_provider: Callable[[], Path],
        list_models: Callable[[Path], Iterable[str]],
        starter_model_path: Callable[[Path], Path],
        starter_model_name: str,
    ) -> None:
        self._conversation = conversation
        self._persona_root_provider = persona_root_provider
        self._fronting_active = fronting_active
        self._models_dir_provider = models_dir_provider
        self._list_models = list_models
        self._starter_model_path = starter_model_path
        self._starter_model_name = starter_model_name

    def insert_banner(self, label: str, body: str) -> None:
        self._conversation.append(f"[{label}] {body}\n")

    def insert_welcome(self) -> None:
        self.insert_banner(
            "welcome",
            "Thank you for trusting Alter/Ego. The README hosts setup notes if you ever feel lost.",
        )
        self.insert_persona_hint()
        self.insert_model_hint()

    def insert_persona_hint(self) -> None:
        persona_root = self._persona_root_provider()
        if not self._persona_files_present(persona_root):
            self.insert_banner(
                "notice",
                (
                    f"No personas found in {persona_root}. Drop `.chaos` or `.mirror.json` files there, or read the persona guidance: "
                    "https://github.com/Autumnus-Labs/AlterEgo#persona-simulation"
                ),
            )
            return

        active = self._fronting_active() or "Rhea"
        self.insert_banner("persona", f"Currently fronting {active}. Personas live in {persona_root}.")

    def insert_model_hint(self) -> None:
        models_dir = self._models_dir_provider()
        models = list(self._list_models(models_dir))
        starter = self._starter_model_path(models_dir)
        if not models:
            self.insert_banner(
                "models",
                (
                    f"Drop GGUF files into {models_dir} to enable GPT4All. We recommend starting with {self._starter_model_name}. "
                    "Read more: https://github.com/Autumnus-Labs/AlterEgo#starter-model"
                ),
            )
        elif not starter.exists():
            self.insert_banner(
                "models",
                (
                    f"Consider downloading the starter model {self._starter_model_name} for the best first-run experience. "
                    f"Store it at {starter}."
                ),
            )
        else:
            self.insert_banner(
                "models",
                f"Models loaded from {models_dir}. Starter model detected: {self._starter_model_name}.",
            )

    @staticmethod
    def _persona_files_present(root: Path) -> bool:
        patterns: Iterable[str] = ("*.chaos", "*.mirror.json")
        return any(any(root.glob(pattern)) for pattern in patterns)


__all__ = [
    "BannerManager",
    "ConversationPane",
    "EntryPanel",
    "MenuBuilder",
    "ModelMenuController",
    "StatusBar",
]
