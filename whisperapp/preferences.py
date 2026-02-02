"""
Preferences window for WhisperApp.
Modern macOS UI with vibrancy effects and native styling.
"""
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_preferences_window = None
_preferences_delegate = None  # Keep delegate alive to prevent GC


def _create_preferences_delegate_class():
    """Create the PyObjC delegate class for handling UI actions."""
    from AppKit import NSObject
    import objc
    
    class PreferencesDelegate(NSObject):
        """Delegate to handle button and popup actions properly via PyObjC."""
        
        def initWithPreferencesWindow_app_(self, prefs_window, app_instance):
            self = objc.super(PreferencesDelegate, self).init()
            if self is None:
                return None
            self.prefs_window = prefs_window
            self.app = app_instance
            return self
        
        @objc.python_method
        def set_model_popup(self, popup):
            """Store reference to model popup for action handler."""
            self._model_popup = popup
        
        @objc.python_method  
        def set_hotkey_button(self, button):
            """Store reference to hotkey button for action handler."""
            self._hotkey_button = button
        
        def recordHotkey_(self, sender):
            """Handle Record Hotkey button click."""
            log.info("Record hotkey button clicked")
            if not self.prefs_window.is_recording_hotkey:
                self.prefs_window.is_recording_hotkey = True
                sender.setTitle_("Press a key...")
                
                # Store sender reference for callback
                button = sender
                prefs = self.prefs_window
                
                def on_key_recorded(key_name):
                    from .hotkey import HotkeyManager
                    display = HotkeyManager.KEY_DISPLAY.get(key_name, key_name)
                    button.setTitle_(display)
                    prefs.is_recording_hotkey = False
                    log.info(f"Hotkey recorded: {key_name} -> {display}")
                
                if self.app.hotkey_manager:
                    self.app.hotkey_manager.start_hotkey_recording(on_key_recorded)
        
        def modelChanged_(self, sender):
            """Handle model popup selection change."""
            from .models import AVAILABLE_MODELS, is_model_downloaded, download_model
            import threading
            
            selected_title = sender.titleOfSelectedItem()
            log.info(f"Model selection changed: {selected_title}")
            
            # Extract model key from selected title
            # Format is "✓ Model Name" or "↓ Model Name"
            model_name = selected_title[2:] if selected_title[:2] in ("✓ ", "↓ ") else selected_title
            
            # Find matching model key
            model_key = None
            for key, info in AVAILABLE_MODELS.items():
                if info.name == model_name:
                    model_key = key
                    break
            
            if not model_key:
                log.warning(f"Could not find model key for: {model_name}")
                return
            
            if model_key == self.app.current_model:
                log.debug("Same model selected, no change needed")
                return
            
            model_info = AVAILABLE_MODELS[model_key]
            
            # Check if downloaded
            if not is_model_downloaded(model_key):
                # Show download prompt
                from AppKit import NSAlert, NSAlertFirstButtonReturn
                
                alert = NSAlert.alloc().init()
                alert.setMessageText_(f"Download {model_info.name}?")
                alert.setInformativeText_(f"Size: {model_info.size}\n\nThis will download the model for offline use.")
                alert.addButtonWithTitle_("Download")
                alert.addButtonWithTitle_("Cancel")
                
                response = alert.runModal()
                
                if response != NSAlertFirstButtonReturn:
                    # User cancelled - revert popup to current model
                    current_info = AVAILABLE_MODELS.get(self.app.current_model)
                    if current_info:
                        downloaded = is_model_downloaded(self.app.current_model)
                        prefix = "✓ " if downloaded else "↓ "
                        sender.selectItemWithTitle_(f"{prefix}{current_info.name}")
                    return
                
                # Download in background
                log.info(f"Starting download of {model_info.name}")
                app = self.app
                popup = sender
                
                def do_download():
                    success = download_model(model_key)
                    if success:
                        app.current_model = model_key
                        # Update popup to show downloaded status
                        popup.selectItemWithTitle_(f"✓ {model_info.name}")
                        # Update the menu item title too
                        for i in range(popup.numberOfItems()):
                            item_title = popup.itemTitleAtIndex_(i)
                            if model_info.name in item_title:
                                popup.itemAtIndex_(i).setTitle_(f"✓ {model_info.name}")
                                break
                        log.info(f"✓ Switched to model: {model_info.name}")
                    else:
                        log.error(f"Failed to download {model_info.name}")
                        # Revert selection
                        current_info = AVAILABLE_MODELS.get(app.current_model)
                        if current_info:
                            downloaded = is_model_downloaded(app.current_model)
                            prefix = "✓ " if downloaded else "↓ "
                            popup.selectItemWithTitle_(f"{prefix}{current_info.name}")
                
                threading.Thread(target=do_download, daemon=True).start()
            else:
                # Already downloaded, just switch
                self.app.current_model = model_key
                log.info(f"✓ Switched to model: {model_info.name}")
        
        def toggleCleanup_(self, sender):
            """Handle AI Formatting toggle."""
            from AppKit import NSOnState
            self.app.cleanup_enabled = (sender.state() == NSOnState)
            status = "ON" if self.app.cleanup_enabled else "OFF"
            log.info(f"AI Formatting toggled: {status}")
    
    return PreferencesDelegate


class PreferencesWindow:
    """Native macOS preferences window with modern vibrancy effects."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.window = None
        self.hotkey_button = None
        self.model_popup = None
        self.is_recording_hotkey = False
        self.delegate = None
    
    def show(self):
        """Show the preferences window."""
        try:
            self._create_window()
        except Exception as e:
            log.error(f"Failed to show preferences: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_window(self):
        """Create the native preferences window with modern styling."""
        global _preferences_delegate
        
        from AppKit import (
            NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
            NSWindowStyleMaskFullSizeContentView, NSBackingStoreBuffered,
            NSScreen, NSView, NSMakeRect, NSTextField, NSButton, 
            NSPopUpButton, NSFont, NSColor, NSApp, NSBox,
            NSImage, NSImageView, NSOnState, NSOffState,
            NSVisualEffectView, NSVisualEffectBlendingModeBehindWindow,
            NSVisualEffectMaterialHUDWindow, NSVisualEffectStateActive,
            NSBezelStyleRounded
        )
        import objc
        
        # Create delegate for button/popup actions
        PreferencesDelegate = _create_preferences_delegate_class()
        self.delegate = PreferencesDelegate.alloc().initWithPreferencesWindow_app_(self, self.app)
        _preferences_delegate = self.delegate  # Prevent garbage collection
        
        # Window dimensions
        win_width = 400
        win_height = 480
        
        # Center on screen
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        x = (screen_frame.size.width - win_width) / 2
        y = (screen_frame.size.height - win_height) / 2
        
        frame = ((x, y), (win_width, win_height))
        
        # Create window with modern styling
        style_mask = (
            NSWindowStyleMaskTitled | 
            NSWindowStyleMaskClosable |
            NSWindowStyleMaskFullSizeContentView
        )
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_("Settings")
        self.window.setTitlebarAppearsTransparent_(True)
        self.window.setTitleVisibility_(1)  # Hidden
        
        # Vibrancy background
        vibrancy_view = NSVisualEffectView.alloc().initWithFrame_(((0, 0), (win_width, win_height)))
        vibrancy_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
        vibrancy_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        vibrancy_view.setState_(NSVisualEffectStateActive)
        
        y_pos = win_height - 45
        
        # === App Header with Icon ===
        assets_dir = Path(__file__).parent / "assets"
        icon_path = assets_dir / "AppIcon.png"
        
        if icon_path.exists():
            image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if image:
                image.setSize_((56, 56))
                image_view = NSImageView.alloc().initWithFrame_(NSMakeRect((win_width - 56) / 2, y_pos - 20, 56, 56))
                image_view.setImage_(image)
                vibrancy_view.addSubview_(image_view)
        
        y_pos -= 70
        
        # App name - centered
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, y_pos, win_width, 24))
        title_label.setStringValue_("WhisperApp")
        title_label.setFont_(NSFont.boldSystemFontOfSize_(18))
        title_label.setTextColor_(NSColor.labelColor())
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setAlignment_(1)  # Center
        vibrancy_view.addSubview_(title_label)
        
        y_pos -= 18
        
        # Version - centered
        version_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, y_pos, win_width, 16))
        version_label.setStringValue_("Version 1.0.0")
        version_label.setFont_(NSFont.systemFontOfSize_(11))
        version_label.setTextColor_(NSColor.tertiaryLabelColor())
        version_label.setBezeled_(False)
        version_label.setDrawsBackground_(False)
        version_label.setEditable_(False)
        version_label.setAlignment_(1)  # Center
        vibrancy_view.addSubview_(version_label)
        
        y_pos -= 25
        
        # === Settings Cards ===
        card_margin = 16
        card_width = win_width - (card_margin * 2)
        
        # --- Model Card ---
        model_card_height = 58
        model_card = self._create_card(card_margin, y_pos - model_card_height, card_width, model_card_height)
        
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(14, model_card_height - 38, 60, 18))
        model_label.setStringValue_("Model")
        model_label.setFont_(NSFont.systemFontOfSize_(13))
        model_label.setTextColor_(NSColor.labelColor())
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        model_card.addSubview_(model_label)
        
        from .models import AVAILABLE_MODELS, is_model_downloaded
        
        self.model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(80, model_card_height - 40, card_width - 100, 26))
        self.model_popup.removeAllItems()
        
        for key, info in AVAILABLE_MODELS.items():
            downloaded = is_model_downloaded(key)
            prefix = "✓ " if downloaded else "↓ "
            self.model_popup.addItemWithTitle_(f"{prefix}{info.name}")
            if key == self.app.current_model:
                self.model_popup.selectItemWithTitle_(f"{prefix}{info.name}")
        
        # Wire up model popup action
        self.model_popup.setTarget_(self.delegate)
        self.model_popup.setAction_(objc.selector(self.delegate.modelChanged_, signature=b'v@:@'))
        self.delegate.set_model_popup(self.model_popup)
        
        model_card.addSubview_(self.model_popup)
        vibrancy_view.addSubview_(model_card)
        
        y_pos -= model_card_height + 10
        
        # --- Hotkey Card ---
        hotkey_card_height = 58
        hotkey_card = self._create_card(card_margin, y_pos - hotkey_card_height, card_width, hotkey_card_height)
        
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(14, hotkey_card_height - 38, 70, 18))
        hotkey_label.setStringValue_("Hotkey")
        hotkey_label.setFont_(NSFont.systemFontOfSize_(13))
        hotkey_label.setTextColor_(NSColor.labelColor())
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        hotkey_card.addSubview_(hotkey_label)
        
        from .hotkey import HotkeyManager
        
        # Get current hotkey display
        current_display = self.app.hotkey_manager.get_trigger_key_display() if self.app.hotkey_manager else "Right ⌘"
        
        # Record Hotkey button
        self.hotkey_button = NSButton.alloc().initWithFrame_(NSMakeRect(90, hotkey_card_height - 40, card_width - 110, 26))
        self.hotkey_button.setTitle_(current_display)
        self.hotkey_button.setBezelStyle_(NSBezelStyleRounded)
        
        # Wire up hotkey button action properly via delegate
        self.hotkey_button.setTarget_(self.delegate)
        self.hotkey_button.setAction_(objc.selector(self.delegate.recordHotkey_, signature=b'v@:@'))
        self.delegate.set_hotkey_button(self.hotkey_button)
        
        hotkey_card.addSubview_(self.hotkey_button)
        vibrancy_view.addSubview_(hotkey_card)
        
        y_pos -= hotkey_card_height + 10
        
        # --- Formatting Card ---
        format_card_height = 58
        format_card = self._create_card(card_margin, y_pos - format_card_height, card_width, format_card_height)
        
        format_label = NSTextField.alloc().initWithFrame_(NSMakeRect(14, format_card_height - 38, 140, 18))
        format_label.setStringValue_("AI Formatting")
        format_label.setFont_(NSFont.systemFontOfSize_(13))
        format_label.setTextColor_(NSColor.labelColor())
        format_label.setBezeled_(False)
        format_label.setDrawsBackground_(False)
        format_label.setEditable_(False)
        format_card.addSubview_(format_label)
        
        # Use NSSwitch for proper macOS toggle appearance (available 10.15+)
        try:
            from AppKit import NSSwitch
            cleanup_switch = NSSwitch.alloc().initWithFrame_(NSMakeRect(card_width - 60, format_card_height - 40, 50, 26))
            cleanup_switch.setState_(NSOnState if self.app.cleanup_enabled else NSOffState)
            
            # Wire up cleanup toggle via delegate
            cleanup_switch.setTarget_(self.delegate)
            cleanup_switch.setAction_(objc.selector(self.delegate.toggleCleanup_, signature=b'v@:@'))
            
            format_card.addSubview_(cleanup_switch)
        except ImportError:
            # Fallback for older macOS - use checkbox with ON/OFF text
            cleanup_btn = NSButton.alloc().initWithFrame_(NSMakeRect(card_width - 60, format_card_height - 40, 50, 26))
            cleanup_btn.setButtonType_(3)  # NSButtonTypeSwitch (checkbox)
            cleanup_btn.setTitle_("ON" if self.app.cleanup_enabled else "OFF")
            cleanup_btn.setState_(NSOnState if self.app.cleanup_enabled else NSOffState)
            cleanup_btn.setTarget_(self.delegate)
            cleanup_btn.setAction_(objc.selector(self.delegate.toggleCleanup_, signature=b'v@:@'))
            format_card.addSubview_(cleanup_btn)
        
        vibrancy_view.addSubview_(format_card)
        
        y_pos -= format_card_height + 10
        
        # --- Shortcuts Info Card ---
        shortcuts_card_height = 100
        shortcuts_card = self._create_card(card_margin, y_pos - shortcuts_card_height, card_width, shortcuts_card_height)
        
        shortcuts_title = NSTextField.alloc().initWithFrame_(NSMakeRect(14, shortcuts_card_height - 28, 200, 18))
        shortcuts_title.setStringValue_("Keyboard Shortcuts")
        shortcuts_title.setFont_(NSFont.boldSystemFontOfSize_(12))
        shortcuts_title.setTextColor_(NSColor.secondaryLabelColor())
        shortcuts_title.setBezeled_(False)
        shortcuts_title.setDrawsBackground_(False)
        shortcuts_title.setEditable_(False)
        shortcuts_card.addSubview_(shortcuts_title)
        
        shortcuts_info = [
            ("Hold hotkey", "Record & transcribe"),
            ("Double-tap", "Paste last transcription"),
            ("Triple-tap", "Undo (Cmd+Z)"),
        ]
        
        row_y = shortcuts_card_height - 48
        for action, desc in shortcuts_info:
            action_label = NSTextField.alloc().initWithFrame_(NSMakeRect(14, row_y, 90, 16))
            action_label.setStringValue_(action)
            action_label.setFont_(NSFont.monospacedSystemFontOfSize_weight_(11, 0.4))
            action_label.setTextColor_(NSColor.labelColor())
            action_label.setBezeled_(False)
            action_label.setDrawsBackground_(False)
            action_label.setEditable_(False)
            shortcuts_card.addSubview_(action_label)
            
            desc_label = NSTextField.alloc().initWithFrame_(NSMakeRect(110, row_y, card_width - 130, 16))
            desc_label.setStringValue_(desc)
            desc_label.setFont_(NSFont.systemFontOfSize_(11))
            desc_label.setTextColor_(NSColor.secondaryLabelColor())
            desc_label.setBezeled_(False)
            desc_label.setDrawsBackground_(False)
            desc_label.setEditable_(False)
            shortcuts_card.addSubview_(desc_label)
            
            row_y -= 20
        
        vibrancy_view.addSubview_(shortcuts_card)
        
        y_pos -= shortcuts_card_height + 10
        
        # === Footer ===
        footer_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 20, win_width, 14))
        footer_label.setStringValue_("Local AI • No data leaves your Mac")
        footer_label.setFont_(NSFont.systemFontOfSize_(10))
        footer_label.setTextColor_(NSColor.tertiaryLabelColor())
        footer_label.setBezeled_(False)
        footer_label.setDrawsBackground_(False)
        footer_label.setEditable_(False)
        footer_label.setAlignment_(1)  # Center
        vibrancy_view.addSubview_(footer_label)
        
        self.window.setContentView_(vibrancy_view)
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        
        log.info("Preferences window opened")
    
    def _create_card(self, x, y, width, height):
        """Create a styled card view with vibrancy."""
        from AppKit import NSVisualEffectView, NSVisualEffectStateActive, NSColor, NSMakeRect
        
        card = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
        card.setMaterial_(3)  # NSVisualEffectMaterialLight
        card.setBlendingMode_(0)  # NSVisualEffectBlendingModeWithinWindow
        card.setState_(NSVisualEffectStateActive)
        card.setWantsLayer_(True)
        card.layer().setCornerRadius_(10)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(0.5)
        card.layer().setBorderColor_(NSColor.separatorColor().CGColor())
        
        return card


def show_preferences(app_instance):
    """Show the preferences window."""
    global _preferences_window
    _preferences_window = PreferencesWindow(app_instance)
    _preferences_window.show()
