# alter_ego_gui.py
# Alter/Ego GUI frontend with full backend + TTS, echo, persona awareness

import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path
import pyttsx3
from alter_shell import AlterShell
from persona_fronting import PersonaFronting

# === Voice Setup ===
voice_engine = pyttsx3.init()
voice_engine.setProperty('rate', 165)
voice_engine.setProperty('volume', 0.9)

# === GUI Class ===
class AlterEgoGUI:
    def __init__(self, root):
        self.shell = AlterShell()
        self.fronting = PersonaFronting()
        self.root = root
        root.title("Alter/Ego")
        root.configure(bg="#1f1f2e")

        self.text_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, width=70, height=25, font=("Consolas", 11),
            bg="#2e2e3f", fg="#dcdcdc", insertbackground="white", borderwidth=0, relief="flat"
        )
        self.text_area.pack(padx=20, pady=10)
        self.text_area.configure(state='disabled')

        self.entry = tk.Entry(root, font=("Consolas", 11), bg="#3c3c50", fg="#ffffff",
                              insertbackground="white", relief="flat")
        self.entry.pack(fill=tk.X, padx=20, pady=(0,10))
        self.entry.bind("<Return>", self.send_input)

        self.text_area.tag_config("user", foreground="#85d6ff")
        self.text_area.tag_config("alter", foreground="#f5b6ff")

    def speak(self, text):
        voice_engine.say(text)
        voice_engine.runAndWait()

    def send_input(self, event=None):
        user_text = self.entry.get().strip()
        if not user_text:
            return

        self.entry.delete(0, tk.END)
        self.display_text(f"You: {user_text}\n", "user")
        response = self.shell.interact(user_text)

        if isinstance(response, str):
            self.display_text(f"{response}\n\n", "alter")
            self.speak(response)

        active_persona = self.fronting.get_active()
        if active_persona:
            self.root.title(f"Alter/Ego — {active_persona}")

    def display_text(self, text, tag):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, text, tag)
        self.text_area.configure(state='disabled')
        self.text_area.yview(tk.END)

# === Launch GUI ===
if __name__ == "__main__":
    root = tk.Tk()
    gui = AlterEgoGUI(root)
    root.mainloop()
