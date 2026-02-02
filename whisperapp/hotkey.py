"""Global hotkey manager and text injection for macOS."""

import threading
import time
from typing import Callable, Optional

from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyperclip


class HotkeyManager:
    """
    Manages global hotkey detection and text injection.
    
    Default behavior: Hold Right Command to record, release to stop.
    """
    
    def __init__(
        self,
        trigger_key: Key = Key.cmd_r,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None
    ):
        """
        Initialize the hotkey manager.
        
        Args:
            trigger_key: The key to use as push-to-talk trigger
            on_start: Callback when key is pressed (start recording)
            on_stop: Callback when key is released (stop recording)
        """
        self.trigger_key = trigger_key
        self.on_start = on_start
        self.on_stop = on_stop
        self.keyboard_controller = Controller()
        self.is_pressed = False
        self.listener: Optional[keyboard.Listener] = None
        self._running = False
    
    def _on_press(self, key):
        """Handle key press events."""
        try:
            if key == self.trigger_key and not self.is_pressed:
                self.is_pressed = True
                if self.on_start:
                    # Run callback in separate thread to not block listener
                    threading.Thread(target=self.on_start, daemon=True).start()
        except Exception as e:
            print(f"Error in key press handler: {e}")
    
    def _on_release(self, key):
        """Handle key release events."""
        try:
            if key == self.trigger_key and self.is_pressed:
                self.is_pressed = False
                if self.on_stop:
                    threading.Thread(target=self.on_stop, daemon=True).start()
        except Exception as e:
            print(f"Error in key release handler: {e}")
    
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
            # Save current clipboard contents
            old_clipboard = pyperclip.paste()
            
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
            
            # Small delay before restoring clipboard
            time.sleep(0.1)
            
            # Optionally restore old clipboard (commented out to keep transcribed text)
            # pyperclip.copy(old_clipboard)
            
            return True
            
        except Exception as e:
            print(f"Error injecting text: {e}")
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


# Mapping of common key names to pynput Key objects
KEY_MAP = {
    'cmd_r': Key.cmd_r,
    'cmd_l': Key.cmd_l,
    'ctrl_r': Key.ctrl_r,
    'ctrl_l': Key.ctrl_l,
    'alt_r': Key.alt_r,
    'alt_l': Key.alt_l,
    'shift_r': Key.shift_r,
    'shift_l': Key.shift_l,
    'fn': Key.f13,  # Fn key varies by keyboard
    'caps_lock': Key.caps_lock,
}


def get_key_from_string(key_name: str) -> Key:
    """Convert a string key name to a pynput Key object."""
    key_name = key_name.lower().replace(' ', '_')
    return KEY_MAP.get(key_name, Key.cmd_r)
