"""
Audio feedback module for WhisperApp.
Uses macOS native NSSound for instant, low-latency playback.
"""
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Sound file location
ASSETS_DIR = Path(__file__).parent / "assets"
DROP_SOUND = ASSETS_DIR / "drop.mp3"

# Pre-loaded sounds for instant playback
_start_sound = None
_stop_sound = None
_initialized = False


def _init_sounds():
    """Pre-load sounds for instant playback."""
    global _start_sound, _stop_sound, _initialized
    
    if _initialized:
        return
    
    if not DROP_SOUND.exists():
        log.warning(f"Sound file not found: {DROP_SOUND}")
        _initialized = True
        return
    
    try:
        from AppKit import NSSound
        
        # Load the sound once for instant playback
        _start_sound = NSSound.alloc().initWithContentsOfFile_byReference_(
            str(DROP_SOUND), True
        )
        
        # For stop sound, we'll use same sound (pitch shift not easily done with NSSound)
        # But we can use a slightly different approach or just accept same sound
        _stop_sound = NSSound.alloc().initWithContentsOfFile_byReference_(
            str(DROP_SOUND), True
        )
        
        if _start_sound and _stop_sound:
            log.debug("✓ Sound effects loaded")
        
        _initialized = True
        
    except ImportError:
        log.warning("AppKit not available - audio feedback disabled")
        _initialized = True
    except Exception as e:
        log.warning(f"Could not load sounds: {e}")
        _initialized = True


def play_start_sound():
    """Play the start recording sound (instant)."""
    _init_sounds()
    if _start_sound:
        try:
            # Stop if already playing, then play
            _start_sound.stop()
            _start_sound.play()
        except Exception as e:
            log.debug(f"Start sound error: {e}")


def play_stop_sound():
    """Play the stop recording sound (instant)."""
    _init_sounds()
    if _stop_sound:
        try:
            # Stop if already playing, then play
            _stop_sound.stop()
            _stop_sound.play()
        except Exception as e:
            log.debug(f"Stop sound error: {e}")


# Pre-initialize on module load for fastest first play
try:
    _init_sounds()
except:
    pass
