# WhisperApp

🎤 **Free, local voice-to-text for macOS** - A privacy-focused alternative to Wispr Flow and SuperWhisper.

## Features

- **Push-to-Talk**: Hold `Right ⌘` to record, release to transcribe
- **Fast & Accurate**: Uses Parakeet-MLX (~0.5s transcription time)
- **Smart Cleanup**: Local Llama 3B removes filler words ("um", "uh", "like")
- **100% Local**: All processing on your Mac - no cloud, no subscriptions
- **Works Everywhere**: Pastes text into any app (Slack, Gmail, VS Code, etc.)
- **History & Stats**: Track your transcriptions and speaking speed

## Requirements

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.10+
- ~3GB disk space for models (downloaded on first run)

## Quick Start

1. Clone or download this folder
2. Double-click `start.command` (or run `./start.command` in Terminal)
3. Grant Accessibility permissions when prompted
4. Hold `Right ⌘` and speak!

## First Run

On first run, WhisperApp will:
1. Create a Python virtual environment
2. Install dependencies
3. Download AI models:
   - Parakeet-MLX (~600MB) - transcription
   - Llama 3.2 3B (~2GB) - filler word cleanup

## Usage

| Action | How |
|--------|-----|
| Record | Hold `Right ⌘` |
| Stop & Transcribe | Release `Right ⌘` |
| View History | Click 🎤 → History |
| View Stats | Click 🎤 → Statistics |
| Toggle Cleanup | Click 🎤 → Use LLM Cleanup |

## Privacy

WhisperApp is **100% local**:
- Audio is processed on your device
- Transcriptions are stored locally in `~/.whisperapp/`
- No internet connection required after model download
- No telemetry or analytics

## Troubleshooting

### "Accessibility access not granted"
Go to: **System Settings → Privacy & Security → Accessibility**  
Enable your terminal app (Terminal, iTerm, etc.)

### "No speech detected"
- Check microphone permissions in System Settings
- Try speaking louder or closer to the mic
- Ensure recording is at least 0.5 seconds

### Slow first transcription
The first transcription is slower while models load into memory. Subsequent transcriptions will be fast (~1 second total).

## License

MIT License - Free for personal and commercial use.
