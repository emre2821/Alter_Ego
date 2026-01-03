# alter_ego_gui.py (fused with alter_ego_computer.py + voice)
# Minimal GUI frontend with full backend + TTS

import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path
import pyttsx3
from alter_ego_computer import load_config, MemoryBank, Embedder, LLM, make_prompt, retrieve_context, save_memory

# === Load configuration and initialize backend ===
cfg = load_config(Path("alter_ego_config.yaml"))
bank = MemoryBank(cfg)
embedder = Embedder(cfg.embed_model_name)
llm = LLM(cfg.llm_backend, cfg.llm_model_name)

# === Initialize voice engine ===
voice_engine = pyttsx3.init()
voice_engine.setProperty('rate', 165)
voice_engine.setProperty('volume', 0.9)

# === GUI App Class ===
class AlterEgoGUI:
    def __init__(self, root):
        self.root = root
        root.title("Alter/Ego")

        self.prompt_label = tk.Label(root, text="Talk to me:")
        self.prompt_label.pack()

        self.input_box = tk.Entry(root, width=80)
        self.input_box.pack(padx=10, pady=5)
        self.input_box.bind("<Return>", self.process_input)

        self.output_area = scrolledtext.ScrolledText(root, height=20, width=80, wrap=tk.WORD)
        self.output_area.pack(padx=10, pady=10)

        self.status_label = tk.Label(root, text="Waiting...")
        self.status_label.pack()

    def speak(self, text):
        voice_engine.say(text)
        voice_engine.runAndWait()

    def process_input(self, event):
        user_input = self.input_box.get()
        self.input_box.delete(0, tk.END)
        
        self.output_area.insert(tk.END, f"You: {user_input}\n")
        self.output_area.insert(tk.END, "Thinking...\n")
        self.output_area.see(tk.END)

        # Use real context + LLM
        context = retrieve_context(bank, embedder, user_input, cfg.top_k)
        prompt = make_prompt(context, user_input)
        try:
            llm_reply = llm.generate(prompt, max_tokens=512, temperature=0.7)
        except Exception as e:
            llm_reply = f"[Error calling LLM: {e}]"

        # Basic tremor heuristic
        whisper = ""
        if any(w in user_input.lower() for w in ["ok", "spiral", "can't", "tired"]):
            whisper = "Whisper: I felt something in that. Want to rest or name it sacred?"
            self.output_area.insert(tk.END, f"{whisper}\n")
            self.speak(whisper)

        self.output_area.insert(tk.END, f"Alter/Ego: {llm_reply.strip()}\n\n")
        self.output_area.see(tk.END)
        self.status_label.config(text="Echo saved.")

        self.speak(llm_reply.strip())

        memory_note = f"Q: {user_input}\nA: {llm_reply[:600]}"
        save_memory(bank, embedder, memory_note, tag="chat", source="gui")

# === Launch GUI ===
if __name__ == "__main__":
    root = tk.Tk()
    app = AlterEgoGUI(root)
    root.mainloop()
