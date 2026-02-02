# Troubleshooting Log

## 2026-02-01: LLM Cleanup Returning Commentary

**Symptom**: Llama 3B model returning conversational text like "Here's the cleaned version:" along with the cleaned transcription.

**Root Cause**: Instruction-tuned models default to conversational responses.

**Fix Applied**:
1. Made prompt stricter with explicit "Output ONLY the formatted text"
2. Added example showing exact expected input/output format
3. Added post-processing regex to strip common commentary patterns
4. Added fallback to regex cleanup if LLM response contains commentary phrases

**File**: `whisperapp/cleanup.py`

---

## 2026-02-01: Pygame Bus Error Crash

**Symptom**: App crashes with "Bus error: 10" when pygame tries to play audio.

**Error**: 
```
/Users/ashtonmiller/Desktop/WhisperApp/start.command: line 74: 45787 Bus error: 10
```

**Root Cause**: pygame's SDL audio initialization conflicts with sounddevice and/or macOS audio subsystem when both are active.

**Fix Applied**: Replaced pygame with macOS native `NSSound` API which:
- Doesn't conflict with other audio APIs
- Has lower latency (sounds pre-loaded)
- Is already available via pyobjc-framework-Cocoa dependency

**File**: `whisperapp/sounds.py`

---

## 2026-02-01: afplay Audio Delay

**Symptom**: Sound plays but with noticeable ~200-300ms delay after button press.

**Root Cause**: `afplay` subprocess has startup latency - must spawn process and load file each time.

**Fix Applied**: Switch to `NSSound` with pre-loading at module import:
```python
_start_sound = NSSound.alloc().initWithContentsOfFile_byReference_(str(DROP_SOUND), True)
```

**Result**: Sounds now play instantly on button press.

**File**: `whisperapp/sounds.py`

---

## 2026-02-01: Processing Hang on First Recording

**Symptom**: First recording after app launch hung for 30+ seconds before transcribing.

**Root Cause**: Lazy imports of `scipy.io.wavfile` - Python imported the large scipy library during the first `recorder.stop()` call.

**Fix Applied**: Move imports to module level in `recorder.py`:
```python
import time
from scipy.io import wavfile
import sounddevice as sd
```

**Result**: Import cost is paid at app startup, not during first recording.

**File**: `whisperapp/recorder.py`

---

## 2026-02-01: Rapid Tap Crash (Race Condition)

**Symptom**: App crashes when user taps hotkey rapidly multiple times.

**Error**: Various race conditions / state inconsistencies.

**Root Cause**: Hotkey callbacks fire on separate thread, multiple events could overlap.

**Fix Applied**:
1. Added `threading.Lock` around `_on_recording_start`
2. Added 100ms debounce (`_last_action_time` check)
3. Added early return if `is_recording` or `is_processing` already True

**File**: `whisperapp/app.py`

---

## 2026-02-01: Audio Stream Resource Leak (Abort Trap: 6)

**Symptom**: App crashes with "Abort trap: 6" and "leaked semaphore objects" after heavy use.

**Root Cause**: Rapid start/stop cycles left audio streams unclosed. Native resources accumulated until crash.

**Fix Applied**:
1. Clean up existing stream before creating new one in `start()`
2. Wrap `stream.stop()`/`stream.close()` in try/except
3. Add `cancel()` method for quick taps that doesn't try to save audio
4. Use `cancel()` in `_on_recording_cancel` instead of `stop()`

**Files**: `whisperapp/recorder.py`, `whisperapp/app.py`

---

## 2026-02-01: Database Argument Error

**Symptom**: "TypeError: Database.save_transcription() got an unexpected keyword argument 'model'"

**Root Cause**: Added extra parameters (`model`, `cleanup_used`) to save call but database schema/method didn't support them.

**Fix Applied**: Removed unsupported arguments from the save_transcription call.

**File**: `whisperapp/app.py`

