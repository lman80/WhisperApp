"""Main WhisperApp menu bar application."""

import os
import sys
import threading
import time
import logging
from typing import Optional

import rumps

from .database import Database
from .recorder import AudioRecorder
from .transcribe import transcribe
from .cleanup import TextCleaner
from .hotkey import HotkeyManager
from .sounds import play_start_sound, play_stop_sound
from .indicator import show_indicator, hide_indicator, update_indicator_level

# Setup logging
DEBUG = os.environ.get('WHISPERAPP_DEBUG', '1') == '1'
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger('whisperapp')


class WhisperApp(rumps.App):
    """
    WhisperApp - Local voice-to-text transcription for macOS.
    
    Lives in the menu bar and provides push-to-talk transcription
    using local Parakeet-MLX for ASR and Llama 3B for filler word cleanup.
    """
    
    def __init__(self):
        log.info("Initializing WhisperApp...")
        
        # Find menu bar icon
        from pathlib import Path
        assets_dir = Path(__file__).parent / "assets"
        icon_path = assets_dir / "MenuBarIcon.png"
        icon = str(icon_path) if icon_path.exists() else None
        
        super().__init__(
            name="WhisperApp",
            icon=icon,
            title=None if icon else "🎤",  # Use icon OR text, not both
            quit_button="Quit WhisperApp"
        )
        
        # Core components
        log.debug("Creating database connection...")
        self.db = Database()
        log.debug("Creating audio recorder...")
        self.recorder = AudioRecorder()
        log.debug("Creating text cleaner...")
        self.cleaner = TextCleaner(use_llm=True)
        self.hotkey_manager: Optional[HotkeyManager] = None
        
        # State
        self.is_recording = False
        self.is_processing = False
        self.current_model = "parakeet"  # Default model
        self._recording_lock = threading.Lock()
        self._last_action_time = 0
        
        # Build menu
        self._build_menu()
        
        # Start hotkey listener in background
        log.info("Starting hotkey listener (Right ⌘)...")
        self._start_hotkey_listener()
        
        # Pre-load models in background (optional, for faster first use)
        log.debug("Starting model preload thread...")
        threading.Thread(target=self._preload_models, daemon=True).start()
        log.info("✓ WhisperApp initialized! Hold Right ⌘ to record.")
    
    def _build_menu(self):
        """Build the menu bar menu."""
        # Build model submenu
        model_menu = self._build_model_menu()
        
        self.menu = [
            rumps.MenuItem("Status: Ready", callback=None),
            None,  # Separator
            model_menu,
            rumps.MenuItem("Cleanup: ON", callback=self._toggle_cleanup),
            None,  # Separator
            rumps.MenuItem("History", callback=self.show_history),
            rumps.MenuItem("Statistics", callback=self.show_statistics),
            rumps.MenuItem("Settings", callback=self.show_settings),
            None,  # Separator
        ]
        
        # Cleanup on by default
        self.cleanup_enabled = True
    
    def _build_model_menu(self):
        """Build the Model selection submenu."""
        from .models import AVAILABLE_MODELS, is_model_downloaded
        
        model_menu = rumps.MenuItem("Model: Parakeet")
        
        for key, info in AVAILABLE_MODELS.items():
            downloaded = is_model_downloaded(key)
            prefix = "✓ " if downloaded else "↓ "
            title = f"{prefix}{info.name} ({info.speed})"
            
            item = rumps.MenuItem(title, callback=self._on_model_select)
            item._model_key = key  # Store key for callback
            
            # Mark current selection
            if key == self.current_model:
                item.state = True
            
            model_menu.add(item)
        
        return model_menu
    
    def _on_model_select(self, sender):
        """Handle model selection from menu."""
        from .models import AVAILABLE_MODELS, is_model_downloaded, download_model
        
        model_key = sender._model_key
        model_info = AVAILABLE_MODELS.get(model_key)
        
        if not model_info:
            return
        
        # Check if downloaded
        if not is_model_downloaded(model_key):
            # Confirm download
            response = rumps.alert(
                title=f"Download {model_info.name}?",
                message=f"Size: {model_info.size}\n\nThis will download the model for offline use.",
                ok="Download",
                cancel="Cancel"
            )
            
            if response != 1:  # Not OK
                return
            
            # Download in background
            self._update_status(f"Downloading {model_info.name}...", "📥")
            
            def do_download():
                success = download_model(model_key)
                if success:
                    self.current_model = model_key
                    self._update_model_menu()
                    self._update_status("Ready", "🎤")
                    log.info(f"Switched to model: {model_info.name}")
                else:
                    self._update_status("Download failed", "⚠️")
            
            threading.Thread(target=do_download, daemon=True).start()
        else:
            # Already downloaded, just switch
            self.current_model = model_key
            self._update_model_menu()
            log.info(f"Switched to model: {model_info.name}")
    
    def _update_model_menu(self):
        """Update model menu checkmarks and title."""
        from .models import AVAILABLE_MODELS, is_model_downloaded
        
        model_info = AVAILABLE_MODELS.get(self.current_model)
        if not model_info:
            return
        
        # Update parent menu title
        try:
            model_menu = self.menu.get("Model: Parakeet") or self.menu.get(f"Model: {model_info.name}")
            if model_menu:
                for item in model_menu.values():
                    if hasattr(item, '_model_key'):
                        item.state = (item._model_key == self.current_model)
        except Exception as e:
            log.debug(f"Could not update model menu: {e}")
    
    def _toggle_cleanup(self, sender):
        """Toggle between raw and cleanup mode."""
        self.cleanup_enabled = not self.cleanup_enabled
        if self.cleanup_enabled:
            sender.title = "Cleanup: ON"
            log.info("Cleanup mode: ON (formatting enabled)")
        else:
            sender.title = "Cleanup: OFF"
            log.info("Cleanup mode: OFF (raw transcription)")
    
    def _start_hotkey_listener(self):
        """Initialize and start the global hotkey listener."""
        self.hotkey_manager = HotkeyManager(
            on_start=self._on_recording_start,
            on_stop=self._on_recording_stop,
            on_cancel=self._on_recording_cancel,
            on_double_tap=self._on_double_tap,
            on_triple_tap=self._on_triple_tap
        )
        self.hotkey_manager.start_listening_async()
    
    def _preload_models(self):
        """Pre-load transcription and cleanup models in background."""
        try:
            log.debug("Pre-loading cleanup model (Llama 3B)...")
            # Pre-warm the cleaner (loads Llama model)
            self.cleaner.initialize()
            log.info("✓ Cleanup model loaded")
        except Exception as e:
            log.warning(f"Could not pre-load models: {e}")
    
    def _update_status(self, status: str, icon: str = "🎤"):
        """Update the menu bar status."""
        self.title = icon
        if "Status:" in self.menu.keys():
            self.menu["Status: Ready"].title = f"Status: {status}"
        else:
            # Find and update the status item
            for item in self.menu.values():
                if hasattr(item, 'title') and item.title.startswith("Status:"):
                    item.title = f"Status: {status}"
                    break
    
    def _on_recording_start(self):
        """Called when the push-to-talk key is pressed."""
        log.info("▶️ Hotkey PRESSED - starting recording")
        
        # Debounce rapid presses (min 100ms between actions)
        import time as time_module
        now = time_module.time()
        if now - self._last_action_time < 0.1:
            log.debug("Debounced - too fast")
            return
        self._last_action_time = now
        
        with self._recording_lock:
            if self.is_processing:
                log.warning("Still processing previous recording, ignoring")
                return
            if self.is_recording:
                log.warning("Already recording, ignoring")
                return
            
            self.is_recording = True
            self._update_status("Recording...", "🔴")
            
            # Play start sound and show indicator
            play_start_sound()
            show_indicator()
            
            try:
                # Wire up level callback for visual indicator
                self.recorder.level_callback = update_indicator_level
                self.recorder.start()
                log.debug("Recording started successfully")
            except Exception as e:
                log.error(f"Error starting recording: {e}")
                self._update_status("Microphone error", "⚠️")
                self.is_recording = False
                hide_indicator()
    
    def _on_recording_cancel(self):
        """Called when a quick tap is detected - cancel the recording."""
        log.info("❌ Quick tap detected - cancelling recording")
        with self._recording_lock:
            if self.is_recording:
                try:
                    self.recorder.stop()
                except:
                    pass
                self.is_recording = False
                hide_indicator()
                self._update_status("Ready", "🎤")
    
    def _on_recording_stop(self):
        """Called when the push-to-talk key is released."""
        log.info("⏹️ Hotkey RELEASED - stopping recording")
        
        if not self.is_recording:
            log.warning("Not recording, ignoring key release")
            return
        
        self.is_recording = False
        self.is_processing = True
        
        # Start a failsafe timer to ensure we never stay stuck
        def failsafe_cleanup():
            if self.is_processing:
                log.warning("Failsafe triggered - forcing cleanup after 30s")
                try:
                    hide_indicator()
                    set_processing_mode(False)
                except:
                    pass
                self.is_processing = False
                self._update_status("Timeout - Ready", "🎤")
        
        failsafe_timer = threading.Timer(30.0, failsafe_cleanup)
        failsafe_timer.daemon = True
        failsafe_timer.start()
        
        try:
            # Update status
            self._update_status("Processing...", "⏳")
            
            # Play stop sound (wrapped in try to prevent blocking)
            try:
                play_stop_sound()
            except Exception as e:
                log.warning(f"Could not play stop sound: {e}")
            
            # Switch indicator to processing mode
            try:
                from .indicator import set_processing_mode
                set_processing_mode(True)
            except Exception as e:
                log.warning(f"Could not set processing mode: {e}")
            
            # Stop recording and get audio file
            log.debug("Stopping recorder...")
            wav_path = self.recorder.stop()
            duration = self.recorder.last_duration
            log.info(f"Recorded {duration:.2f}s to {wav_path}")
            
            # Transcribe audio
            from .models import AVAILABLE_MODELS
            model_info = AVAILABLE_MODELS.get(self.current_model)
            model_name = model_info.name if model_info else self.current_model
            log.info(f"Transcribing with {model_name}...")
            raw_text = transcribe(wav_path, model_key=self.current_model)
            log.info(f"Raw transcription: '{raw_text}'")
            
            if not raw_text:
                log.warning("No speech detected in audio")
                self._update_status("No speech detected", "🎤")
                hide_indicator()
                set_processing_mode(False)
                failsafe_timer.cancel()
                return
            
            # Clean up transcription if enabled
            if self.cleanup_enabled:
                log.info("Cleaning with AI (formatting, grammar, quotes)...")
                cleaned_text = self.cleaner.clean(raw_text)
                log.info(f"Cleaned: '{cleaned_text}'")
            else:
                cleaned_text = raw_text
                log.info("Cleanup: OFF (raw)")
            
            # Save to history
            self.db.save_transcription(
                text=cleaned_text,
                raw_text=raw_text,
                duration=duration,
                model=self.current_model,
                cleanup_used=self.cleanup_enabled
            )
            log.debug("Saved to database")
            
            # Store for double-tap paste
            self.hotkey_manager.store_last_transcription(cleaned_text)
            
            # Inject text into active application
            log.info(f"Injecting text: '{cleaned_text}'")
            self.hotkey_manager.inject_text(cleaned_text)
            
            # Update status with word count
            word_count = len(cleaned_text.split())
            log.info(f"✓ Complete! Typed {word_count} words")
            self._update_status(f"Typed {word_count} words", "✓")
            
            # Hide indicator now that we're done
            hide_indicator()
            set_processing_mode(False)
            
            # Reset status after a delay
            threading.Timer(2.0, lambda: self._update_status("Ready", "🎤")).start()
            
            # Clean up temp file
            try:
                os.remove(wav_path)
            except:
                pass
                
        except Exception as e:
            log.error(f"Error processing recording: {e}", exc_info=True)
            self._update_status(f"Error: {str(e)[:20]}", "⚠️")
            try:
                hide_indicator()
                set_processing_mode(False)
            except:
                pass
        finally:
            failsafe_timer.cancel()
            self.is_processing = False
    
    def _on_double_tap(self):
        """Called on double-tap - paste last transcription."""
        log.info("🔄 Double-tap detected - pasting last transcription")
        if self.hotkey_manager:
            self.hotkey_manager.paste_last_transcription()
            self._update_status("Pasted last", "📋")
            threading.Timer(1.5, lambda: self._update_status("Ready", "🎤")).start()
    
    def _on_triple_tap(self):
        """Called on triple-tap - undo last paste."""
        log.info("↩️ Triple-tap detected - undo")
        if self.hotkey_manager:
            self.hotkey_manager.undo_last_paste()
            self._update_status("Undo", "↩️")
            threading.Timer(1.5, lambda: self._update_status("Ready", "🎤")).start()
    
    @rumps.clicked("History")
    def show_history(self, _):
        """Show the transcription history window."""
        from .history_window import show_history_window
        show_history_window(self.db)
    
    @rumps.clicked("Statistics")
    def show_statistics(self, _):
        """Show the statistics window."""
        from .statistics_window import show_statistics_window
        stats = self.db.get_statistics()
        show_statistics_window(stats)
    
    @rumps.clicked("Settings")
    def show_settings(self, _):
        """Show the preferences window."""
        from .preferences import show_preferences
        show_preferences(self)


def main():
    """Entry point for the application."""
    app = WhisperApp()
    app.run()


if __name__ == "__main__":
    main()
