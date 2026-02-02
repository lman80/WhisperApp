# Decisions Log

## 2026-02-01: Cleanup Mode Simplification

**Context**: Originally implemented 4 cleanup modes (Off, Light, Medium, Full Rewrite).

**Decision**: Simplified to just 2 modes - "Raw" and "Cleanup (ON/OFF)".

**Rationale**: 
- User found multiple modes confusing
- The key value is either having formatting or not
- Single toggle is faster to use during dictation workflows

**Alternative considered**: Keep granular modes but default to simple. Rejected because it adds UI complexity without clear benefit.

---

## 2026-02-01: LLM Prompt for Dialogue Formatting

**Context**: User wanted transcription to include proper quotation marks around dialogue.

**Decision**: Changed LLM prompt to explicitly include dialogue formatting with example:
```
Example:
Input: he said what are you doing here I said I dont know
Output: He said, "What are you doing here?" I said, "I don't know."
```

**Rationale**: Few-shot examples are more reliable than instructions alone for formatting tasks.

---

## 2026-02-01: Audio Feedback Sound System

**Context**: User wanted audio feedback when starting/stopping recording.

**Decision**: Use macOS native `NSSound` API via PyObjC (already a dependency).

**Alternatives rejected**:
1. **pygame**: Caused "Bus error: 10" crash - conflicts with audio subsystem
2. **afplay subprocess**: Works but has ~200-300ms startup latency

**Final approach**: Pre-load sounds at module import using `NSSound.alloc().initWithContentsOfFile_byReference_()` for instant playback.

---

## 2026-02-01: Recording Lock and Debounce Architecture

**Context**: Rapid tapping of the Right ⌘ hotkey caused race conditions and crashes.

**Decision**: Implement a two-layer protection system:
1. **Thread lock** (`threading.Lock`) around recording start/stop operations
2. **100ms debounce** - ignore hotkey events within 100ms of last action

**Rationale**: The hotkey callback fires on every key event, and rapid taps can overlap with processing from previous tap. Lock ensures serialization, debounce prevents unnecessary processing.

---

## 2026-02-01: Failsafe Timer for Processing

**Context**: App could hang indefinitely if transcription or cleanup blocked.

**Decision**: Add 30-second failsafe timer that forces UI cleanup regardless of processing state.

**Rationale**: User experience is paramount - even if something goes wrong internally, the app should recover to a usable state.

**Trade-off**: May sometimes cancel legitimate long operations, but prevents app from appearing frozen.

---

## 2026-02-01: Separate cancel() vs stop() for Recorder

**Context**: Quick taps were calling stop() which tried to save an empty WAV file.

**Decision**: Create separate `recorder.cancel()` method for quick tap cleanup.

**Rationale**: Different intents require different cleanup:
- `stop()` = User finished recording, save the audio
- `cancel()` = User didn't intend to record, just release resources

