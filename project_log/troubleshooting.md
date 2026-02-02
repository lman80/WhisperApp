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
