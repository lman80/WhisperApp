# Learnings Log

## 2026-02-01: macOS Audio APIs

**Learning**: For macOS menu bar apps, prefer native APIs over cross-platform libraries.

| Approach | Latency | Stability | Dependencies |
|----------|---------|-----------|--------------|
| pygame | High | Crashes with sounddevice | pygame (large) |
| afplay subprocess | Medium (~200ms) | Stable | None |
| NSSound (AppKit) | Very low | Stable | pyobjc (already have) |

**Best practice**: Use `NSSound` for UI feedback sounds in macOS Python apps.

---

## 2026-02-01: LLM Few-Shot Examples Beat Instructions

**Learning**: For formatting tasks with LLMs, a single clear example is more effective than multiple bullet-point instructions.

**Before** (verbose instructions):
```
- Fix grammar and punctuation
- Add quotation marks around dialogue
- Remove filler words
```

**After** (example-based):
```
Example:
Input: he said what are you doing here
Output: He said, "What are you doing here?"
```

**Why**: Models learn patterns better from examples than from procedural instructions.

---

## 2026-02-01: Sound File Location Convention

**Learning**: Place asset files in `<package>/assets/` directory and reference via `Path(__file__).parent / "assets"`.

This ensures:
- Assets are included when package is installed
- Relative paths work regardless of working directory
- Clear separation of code vs. resources

**Structure**:
```
whisperapp/
├── __init__.py
├── app.py
├── sounds.py
└── assets/
    └── drop.mp3
```

---

## 2026-02-01: Python Lazy Import Performance Impact

**Learning**: Imports inside functions ("lazy imports") can cause significant first-call delays.

**Example**: scipy takes ~30 seconds to import. If imported inside `stop()`:
```python
def stop(self):
    from scipy.io import wavfile  # 30 second delay on FIRST call only
```

**Best practice**: Import heavy libraries at module level so the cost is paid at startup, not during user actions:
```python
from scipy.io import wavfile  # Import once at module load
```

**Trade-off**: Slower app startup, but consistent response time during use.

---

## 2026-02-01: Thread Safety Pattern for Hotkey Callbacks

**Learning**: Hotkey/keyboard callbacks fire on background threads - always assume concurrent access.

**Pattern**:
```python
self._recording_lock = threading.Lock()
self._last_action_time = 0

def _on_hotkey(self):
    # Debounce rapid events
    now = time.time()
    if now - self._last_action_time < 0.1:
        return
    self._last_action_time = now
    
    # Serialize access to shared state
    with self._recording_lock:
        if self.is_processing:
            return
        # ... do work
```

---

## 2026-02-01: Resource Cleanup Pattern for Audio Streams

**Learning**: Audio hardware resources (streams, devices) must be explicitly closed or they leak.

**Pattern for streams**:
```python
def start(self):
    # Always clean up before creating new
    if self.stream:
        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass
        self.stream = None
    
    # Now create new
    self.stream = sd.InputStream(...)
```

**Key insight**: Wrap cleanup in try/except - a stream in error state shouldn't prevent new stream creation.
