# tests/test_echo_emotion.py
from echo_whisper_layer import analyze_emotion

def test_emotion_parse_basic():
    sample = "I don't know if I can do this anymore."
    echo = analyze_emotion(sample)
    assert isinstance(echo, dict) or echo is not None
