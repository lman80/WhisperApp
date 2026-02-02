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
