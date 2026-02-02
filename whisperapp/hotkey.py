"""Global hotkey manager with tap detection and text injection for macOS."""

import threading
import time
import json
from pathlib import Path
from typing import Callable, Optional
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
    
    def __init__(
        self,
        trigger_key: Key = Key.cmd_r,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_double_tap: Optional[Callable] = None,
        on_triple_tap: Optional[Callable] = None
    ):
        """
        Initialize the hotkey manager.
        
        Args:
            trigger_key: The key to use as push-to-talk trigger
            on_start: Callback when key is pressed (start recording)
            on_stop: Callback when key is released (stop recording)
            on_double_tap: Callback for double-tap (paste last transcription)
            on_triple_tap: Callback for triple-tap (undo)
        """
        self.trigger_key = trigger_key
        self.trigger_key_name = 'cmd_r'  # Track name for config
        self.on_start = on_start
        self.on_stop = on_stop
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
        self.was_held = False
        
        # Last transcription for double-tap paste
        self.last_transcription = ""
        
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
    
    def set_trigger_key(self, key_name: str):
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
    
    def _on_press(self, key):
        """Handle key press events."""
        try:
            if key == self.trigger_key and not self.is_pressed:
                self.is_pressed = True
                self.press_start_time = time.time()
                self.was_held = False
        except Exception as e:
            log.error(f"Error in key press handler: {e}")
    
    def _on_release(self, key):
        """Handle key release events with tap detection."""
        try:
            if key == self.trigger_key and self.is_pressed:
                self.is_pressed = False
                press_duration = time.time() - self.press_start_time
                current_time = time.time()
                
                # Was this a hold (for recording) or a tap?
                if press_duration >= self.hold_threshold:
                    # This was a hold - trigger recording stop
                    self.was_held = True
                    self.tap_times = []  # Reset tap counter
                    if self.on_stop:
                        threading.Thread(target=self.on_stop, daemon=True).start()
                else:
                    # This was a quick tap
                    self.tap_times.append(current_time)
                    
                    # Filter out old taps
                    self.tap_times = [t for t in self.tap_times if current_time - t < self.tap_threshold * 3]
                    
                    # Check for triple tap first
                    recent_taps = [t for t in self.tap_times if current_time - t < self.tap_threshold * 2.5]
                    
                    if len(recent_taps) >= 3:
                        log.info("Triple tap detected - undo")
                        self.tap_times = []
                        if self.on_triple_tap:
                            threading.Thread(target=self.on_triple_tap, daemon=True).start()
                    elif len(recent_taps) >= 2:
                        # Wait briefly to see if a third tap is coming
                        def check_double_tap():
                            time.sleep(self.tap_threshold)
                            if len(self.tap_times) == 2:  # Still only 2 taps
                                log.info("Double tap detected - paste last")
                                self.tap_times = []
                                if self.on_double_tap:
                                    self.on_double_tap()
                        threading.Thread(target=check_double_tap, daemon=True).start()
                        
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
        """Undo by selecting all and deleting (Cmd+Z)."""
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
