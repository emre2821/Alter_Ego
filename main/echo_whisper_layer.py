"""
echo_whisper_layer.py
Local minimal adapter/stub for emotion analysis.
If Lyss.modules.emotional_parser is present, Alter_Ego imports that directly.
This module exists so local tests/imports do not fail when Lyss isn't available.
"""

from typing import Dict


def analyze_emotion(text: str) -> Dict[str, float]:
    text_l = (text or "").lower()
    keys = {
        "joy": ["yay", "glad", "happy", "love", "win"],
        "sad": ["sad", "down", "tired", "hurt", "cry"],
        "anger": ["mad", "angry", "furious", "pissed", "rage"],
        "fear": ["scared", "anxious", "nervous", "worried", "afraid"],
    }
    scores = {k: float(sum(1 for w in ws if w in text_l)) for k, ws in keys.items()}
    total = sum(scores.values()) or 1.0
    return {k: v / total for k, v in scores.items()}

