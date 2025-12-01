# TTS Engines

Alter/Ego uses [pyttsx3](https://github.com/nateshmbhat/pyttsx3) as its text-to-speech backend, which provides cross-platform support by interfacing with platform-native speech engines.

## Supported Engines

### Windows
- **SAPI5** (Speech API 5): The default Windows speech engine
- Uses voices installed via Windows Settings > Time & Language > Speech

### macOS
- **NSSpeechSynthesizer**: Native macOS speech synthesis
- Uses voices available in System Preferences > Accessibility > Speech

### Linux
- **espeak**: Open-source speech synthesizer
- Install via: `sudo apt-get install espeak`

## Basic Usage

```python
from alter_ego import AlterEgo

# Initialize with default settings
bot = AlterEgo()
bot.speak("Hello, world!")
```

## Advanced Configuration

You can pass engine-specific parameters when initializing:

```python
from alter_ego import AlterEgo

# Pass engine initialization arguments
bot = AlterEgo(driverName='sapi5')  # Windows
# bot = AlterEgo(driverName='nsss')  # macOS
# bot = AlterEgo(driverName='espeak')  # Linux
```

## Voice Selection

To list available voices and select a specific one:

```python
import pyttsx3

engine = pyttsx3.init()

# List available voices
voices = engine.getProperty('voices')
for voice in voices:
    print(f"ID: {voice.id}")
    print(f"Name: {voice.name}")
    print("---")

# Set a specific voice
engine.setProperty('voice', voices[0].id)
```

## Adjusting Speech Properties

```python
import pyttsx3

engine = pyttsx3.init()

# Adjust speech rate (words per minute)
engine.setProperty('rate', 150)  # Default is usually 200

# Adjust volume (0.0 to 1.0)
engine.setProperty('volume', 0.9)

engine.say("This is a test.")
engine.runAndWait()
```

## Troubleshooting

### Linux: No audio output
Ensure espeak is installed:
```bash
sudo apt-get install espeak
```

### macOS: Permission denied
Grant Terminal (or your IDE) access to speech synthesis in System Preferences > Security & Privacy > Privacy > Accessibility.

### Windows: No voices available
Install additional voices via Windows Settings > Time & Language > Speech > Add voices.
