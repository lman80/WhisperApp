"""Global hotkey manager with tap detection and text injection for macOS."""

import threading
import time
import json
from pathlib import Path
from typing import Callable, Optional, Any
import logging

from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyperclip

log = logging.getLogger(__name__)

# Config file path
CONFIG_PATH = Path.home() / ".whisperapp" / "config.json"


class HotkeyManager:
    """
    Manages global hotkey detection and text injection.
    
    Features:
    - Hold trigger key to record
    - Double-tap to paste last transcription
    - Triple-tap to undo (select all + delete)
    - Record custom hotkey
    """
    
    # Mapping of key names to pynput Key objects
    KEY_MAP = {
        'cmd_r': Key.cmd_r,
        'cmd_l': Key.cmd_l,
        'ctrl_r': Key.ctrl_r,
        'ctrl_l': Key.ctrl_l,
        'alt_r': Key.alt_r,
        'alt_l': Key.alt_l,
        'shift_r': Key.shift_r,
        'shift_l': Key.shift_l,
        'caps_lock': Key.caps_lock,
    }
    
    # Display names for keys
    KEY_DISPLAY = {
        'cmd_r': 'Right ⌘',
        'cmd_l': 'Left ⌘',
        'ctrl_r': 'Right ⌃',
        'ctrl_l': 'Left ⌃',
        'alt_r': 'Right ⌥',
        'alt_l': 'Left ⌥',
        'shift_r': 'Right ⇧',
        'shift_l': 'Left ⇧',
        'caps_lock': '⇪ Caps Lock',
    }
    
    # Reverse map: Key -> name
    KEY_TO_NAME = {v: k for k, v in KEY_MAP.items()}
    
    def __init__(
        self,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        on_double_tap: Optional[Callable] = None,
        on_triple_tap: Optional[Callable] = None
    ):
        """
        Initialize the hotkey manager.
        
        Args:
            on_start: Callback when key is pressed (start recording)
            on_stop: Callback when key is released after holding (stop recording)
            on_cancel: Callback when recording should be cancelled (quick tap)
            on_double_tap: Callback for double-tap (paste last transcription)
            on_triple_tap: Callback for triple-tap (undo)
        """
        self.trigger_key = Key.cmd_r
        self.trigger_key_name = 'cmd_r'
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_cancel = on_cancel
        self.on_double_tap = on_double_tap
        self.on_triple_tap = on_triple_tap
        
        self.keyboard_controller = Controller()
        self.is_pressed = False
        self.listener: Optional[keyboard.Listener] = None
        self._running = False
        
        # Tap detection
        self.tap_times = []
        self.tap_threshold = 0.35  # Max time between taps (seconds)
        self.hold_threshold = 0.25  # Min hold time for recording (seconds)
        self.press_start_time = 0
        self.recording_started = False
        
        # Last transcription for double-tap paste
        self.last_transcription = ""
        
        # Hotkey recording mode
        self.is_recording_hotkey = False
        self.hotkey_record_callback: Optional[Callable[[str], None]] = None
        
        # Load config
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if CONFIG_PATH.exists():
                config = json.loads(CONFIG_PATH.read_text())
                key_name = config.get('trigger_key', 'cmd_r')
                if key_name in self.KEY_MAP:
                    self.trigger_key = self.KEY_MAP[key_name]
                    self.trigger_key_name = key_name
                    log.info(f"Loaded hotkey config: {key_name}")
        except Exception as e:
            log.warning(f"Could not load config: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            config = {'trigger_key': self.trigger_key_name}
            
            # Load existing config and merge
            if CONFIG_PATH.exists():
                try:
                    existing = json.loads(CONFIG_PATH.read_text())
                    existing.update(config)
                    config = existing
                except:
                    pass
            
            CONFIG_PATH.write_text(json.dumps(config, indent=2))
            log.info(f"Saved hotkey config: {self.trigger_key_name}")
        except Exception as e:
            log.error(f"Could not save config: {e}")
    
    def set_trigger_key(self, key_name: str) -> bool:
        """Change the trigger key."""
        if key_name in self.KEY_MAP:
            self.trigger_key = self.KEY_MAP[key_name]
            self.trigger_key_name = key_name
            self.save_config()
            log.info(f"Trigger key changed to: {key_name}")
            return True
        return False
    
    def get_trigger_key_display(self) -> str:
        """Get display name for current trigger key."""
        return self.KEY_DISPLAY.get(self.trigger_key_name, self.trigger_key_name)
    
    def start_hotkey_recording(self, callback: Callable[[str], None]):
        """Start listening for a new hotkey. Callback receives the key name."""
        log.info("Started hotkey recording mode")
        self.is_recording_hotkey = True
        self.hotkey_record_callback = callback
    
    def stop_hotkey_recording(self):
        """Stop hotkey recording mode."""
        self.is_recording_hotkey = False
        self.hotkey_record_callback = None
    
    def _on_press(self, key):
        """Handle key press events."""
        try:
            # Hotkey recording mode - capture any modifier key press
            if self.is_recording_hotkey:
                key_name = self.KEY_TO_NAME.get(key)
                if key_name:
                    log.info(f"Recorded new hotkey: {key_name}")
                    self.set_trigger_key(key_name)
                    self.is_recording_hotkey = False
                    if self.hotkey_record_callback:
                        self.hotkey_record_callback(key_name)
                        self.hotkey_record_callback = None
                return
            
            # Normal mode - detect trigger key press
            if key == self.trigger_key and not self.is_pressed:
                self.is_pressed = True
                self.press_start_time = time.time()
                self.recording_started = False
                
                # Start recording immediately
                if self.on_start:
                    self.recording_started = True
                    threading.Thread(target=self.on_start, daemon=True).start()
        except Exception as e:
            log.error(f"Error in key press handler: {e}")
    
    def _on_release(self, key):
        """Handle key release events with tap detection."""
        try:
            # Skip if in hotkey recording mode
            if self.is_recording_hotkey:
                return
            
            if key == self.trigger_key and self.is_pressed:
                self.is_pressed = False
                press_duration = time.time() - self.press_start_time
                current_time = time.time()
                
                # Was this a hold (for recording) or a tap?
                if press_duration >= self.hold_threshold:
                    # This was a hold - trigger recording stop
                    self.tap_times = []  # Reset tap counter
                    if self.on_stop:
                        threading.Thread(target=self.on_stop, daemon=True).start()
                else:
                    # This was a quick tap
                    # First, always cancel any recording that started
                    if self.recording_started and self.on_cancel:
                        self.on_cancel()  # Call synchronously to ensure state is clean
                    self.recording_started = False
                    
                    # Track tap for double/triple detection
                    self.tap_times.append(current_time)
                    
                    # Filter out old taps
                    self.tap_times = [t for t in self.tap_times if current_time - t < self.tap_threshold * 3]
                    
                    # Get recent taps count
                    recent_taps = [t for t in self.tap_times if current_time - t < self.tap_threshold * 2.5]
                    tap_count = len(recent_taps)
                    
                    if tap_count >= 3:
                        # Triple tap - immediate action
                        log.info("Triple tap detected - undo")
                        self.tap_times = []
                        if self.on_triple_tap:
                            threading.Thread(target=self.on_triple_tap, daemon=True).start()
                    elif tap_count == 2:
                        # Might be double tap - wait to see if a third tap is coming
                        tap_id = len(self.tap_times)  # Track which tap we're waiting on
                        
                        def check_double_tap():
                            time.sleep(self.tap_threshold + 0.05)
                            # Only trigger if no new taps have been added
                            if len(self.tap_times) == tap_id:
                                log.info("Double tap detected - paste last")
                                self.tap_times = []
                                if self.on_double_tap:
                                    self.on_double_tap()
                        
                        threading.Thread(target=check_double_tap, daemon=True).start()
                    # Single tap does nothing extra, recording was already cancelled
                        
        except Exception as e:
            log.error(f"Error in key release handler: {e}")
    
    def store_last_transcription(self, text: str):
        """Store the last transcription for double-tap paste."""
        self.last_transcription = text
    
    def paste_last_transcription(self):
        """Paste the last transcription."""
        if self.last_transcription:
            log.info(f"Pasting last transcription: {self.last_transcription[:50]}...")
            self.inject_text(self.last_transcription)
        else:
            log.info("No previous transcription to paste")
    
    def undo_last_paste(self):
        """Undo by executing Cmd+Z."""
        try:
            log.info("Executing undo (Cmd+Z)")
            self.keyboard_controller.press(Key.cmd)
            time.sleep(0.01)
            self.keyboard_controller.tap('z')
            time.sleep(0.01)
            self.keyboard_controller.release(Key.cmd)
        except Exception as e:
            log.error(f"Error in undo: {e}")
    
    def inject_text(self, text: str) -> bool:
        """
        Inject text into the active application via clipboard + Cmd+V.
        
        Args:
            text: Text to paste into the active application
            
        Returns:
            True if successful, False otherwise
        """
        if not text:
            return False
        
        try:
            # Copy new text to clipboard
            pyperclip.copy(text)
            
            # Small delay to ensure clipboard is ready
            time.sleep(0.05)
            
            # Simulate Cmd+V
            self.keyboard_controller.press(Key.cmd)
            time.sleep(0.01)
            self.keyboard_controller.tap('v')
            time.sleep(0.01)
            self.keyboard_controller.release(Key.cmd)
            
            return True
            
        except Exception as e:
            log.error(f"Error injecting text: {e}")
            return False
    
    def start_listening(self) -> None:
        """Start listening for global hotkeys (blocking)."""
        self._running = True
        
        with keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        ) as listener:
            self.listener = listener
            listener.join()
    
    def start_listening_async(self) -> threading.Thread:
        """Start listening for global hotkeys in a background thread."""
        thread = threading.Thread(target=self.start_listening, daemon=True)
        thread.start()
        return thread
    
    def stop_listening(self) -> None:
        """Stop the hotkey listener."""
        self._running = False
        if self.listener:
            self.listener.stop()


def get_key_from_string(key_name: str) -> Key:
    """Convert a string key name to a pynput Key object."""
    key_name = key_name.lower().replace(' ', '_')
    return HotkeyManager.KEY_MAP.get(key_name, Key.cmd_r)
