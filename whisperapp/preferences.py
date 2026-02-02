"""
Preferences window for WhisperApp.
Native macOS preferences UI with model selection, cleanup toggle, and about info.
"""
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_preferences_window = None


class PreferencesWindow:
    """Native macOS preferences window."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.window = None
    
    def show(self):
        """Show the preferences window."""
        try:
            self._create_window()
        except Exception as e:
            log.error(f"Failed to show preferences: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_window(self):
        """Create the native preferences window."""
        from AppKit import (
            NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
            NSBackingStoreBuffered, NSScreen, NSView, NSMakeRect,
            NSTextField, NSButton, NSPopUpButton, NSFont, NSColor, NSApp,
            NSBox, NSBezelStyleRounded, NSOnState, NSOffState,
            NSImage, NSImageView
        )
        from PyObjCTools import AppHelper
        import objc
        
        # Window dimensions
        win_width = 450
        win_height = 350
        
        # Center on screen
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        x = (screen_frame.size.width - win_width) / 2
        y = (screen_frame.size.height - win_height) / 2
        
        frame = ((x, y), (win_width, win_height))
        
        # Create window
        style_mask = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_("WhisperApp Preferences")
        
        # Content view
        content_view = NSView.alloc().initWithFrame_(((0, 0), (win_width, win_height)))
        
        y_pos = win_height - 50
        
        # === App Icon and Title ===
        assets_dir = Path(__file__).parent / "assets"
        icon_path = assets_dir / "AppIcon.png"
        if icon_path.exists():
            image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if image:
                image.setSize_((64, 64))
                image_view = NSImageView.alloc().initWithFrame_(NSMakeRect(20, y_pos - 20, 64, 64))
                image_view.setImage_(image)
                content_view.addSubview_(image_view)
        
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(100, y_pos + 10, 200, 24))
        title_label.setStringValue_("WhisperApp")
        title_label.setFont_(NSFont.boldSystemFontOfSize_(20))
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        content_view.addSubview_(title_label)
        
        version_label = NSTextField.alloc().initWithFrame_(NSMakeRect(100, y_pos - 12, 200, 18))
        version_label.setStringValue_("Version 1.0.0")
        version_label.setFont_(NSFont.systemFontOfSize_(12))
        version_label.setTextColor_(NSColor.grayColor())
        version_label.setBezeled_(False)
        version_label.setDrawsBackground_(False)
        version_label.setEditable_(False)
        content_view.addSubview_(version_label)
        
        y_pos -= 100
        
        # === Divider ===
        divider = NSBox.alloc().initWithFrame_(NSMakeRect(20, y_pos, win_width - 40, 1))
        divider.setBoxType_(2)  # NSSeparator
        content_view.addSubview_(divider)
        
        y_pos -= 40
        
        # === Model Selection ===
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 100, 20))
        model_label.setStringValue_("Model:")
        model_label.setFont_(NSFont.boldSystemFontOfSize_(13))
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        content_view.addSubview_(model_label)
        
        from .models import AVAILABLE_MODELS, is_model_downloaded
        
        model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(120, y_pos - 3, 280, 26))
        model_popup.removeAllItems()
        
        for key, info in AVAILABLE_MODELS.items():
            downloaded = is_model_downloaded(key)
            prefix = "✓ " if downloaded else "↓ "
            model_popup.addItemWithTitle_(f"{prefix}{info.name}")
            if key == self.app.current_model:
                model_popup.selectItemWithTitle_(f"{prefix}{info.name}")
        
        content_view.addSubview_(model_popup)
        
        y_pos -= 40
        
        # === Cleanup Toggle ===
        cleanup_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 100, 20))
        cleanup_label.setStringValue_("Text Cleanup:")
        cleanup_label.setFont_(NSFont.boldSystemFontOfSize_(13))
        cleanup_label.setBezeled_(False)
        cleanup_label.setDrawsBackground_(False)
        cleanup_label.setEditable_(False)
        content_view.addSubview_(cleanup_label)
        
        cleanup_btn = NSButton.alloc().initWithFrame_(NSMakeRect(120, y_pos - 2, 150, 24))
        cleanup_btn.setButtonType_(3)  # Switch/toggle button
        cleanup_btn.setTitle_("AI Formatting")
        cleanup_btn.setState_(NSOnState if self.app.cleanup_enabled else NSOffState)
        
        def toggle_cleanup(sender):
            self.app.cleanup_enabled = (sender.state() == NSOnState)
            # Update menu item
            for item in self.app.menu.values():
                if hasattr(item, 'title') and 'Cleanup' in str(item.title):
                    item.title = f"Cleanup: {'ON' if self.app.cleanup_enabled else 'OFF'}"
                    break
        
        cleanup_btn.setTarget_(cleanup_btn)
        cleanup_btn.setAction_(objc.selector(toggle_cleanup, signature=b'v@:@'))
        content_view.addSubview_(cleanup_btn)
        
        y_pos -= 50
        
        # === Hotkey Info ===
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 100, 20))
        hotkey_label.setStringValue_("Hotkey:")
        hotkey_label.setFont_(NSFont.boldSystemFontOfSize_(13))
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        content_view.addSubview_(hotkey_label)
        
        hotkey_value = NSTextField.alloc().initWithFrame_(NSMakeRect(120, y_pos, 200, 20))
        hotkey_value.setStringValue_("Hold Right ⌘ (Command)")
        hotkey_value.setFont_(NSFont.systemFontOfSize_(13))
        hotkey_value.setBezeled_(False)
        hotkey_value.setDrawsBackground_(False)
        hotkey_value.setEditable_(False)
        content_view.addSubview_(hotkey_value)
        
        y_pos -= 50
        
        # === Divider ===
        divider2 = NSBox.alloc().initWithFrame_(NSMakeRect(20, y_pos, win_width - 40, 1))
        divider2.setBoxType_(2)
        content_view.addSubview_(divider2)
        
        y_pos -= 30
        
        # === Credits ===
        credits_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, win_width - 40, 18))
        credits_label.setStringValue_("Local AI transcription • No data leaves your Mac")
        credits_label.setFont_(NSFont.systemFontOfSize_(11))
        credits_label.setTextColor_(NSColor.grayColor())
        credits_label.setBezeled_(False)
        credits_label.setDrawsBackground_(False)
        credits_label.setEditable_(False)
        credits_label.setAlignment_(1)  # Center
        content_view.addSubview_(credits_label)
        
        # Close button
        close_btn = NSButton.alloc().initWithFrame_(NSMakeRect(win_width - 90, 15, 70, 30))
        close_btn.setTitle_("Close")
        close_btn.setBezelStyle_(NSBezelStyleRounded)
        close_btn.setTarget_(self.window)
        close_btn.setAction_(objc.selector(self.window.close, signature=b'v@:'))
        content_view.addSubview_(close_btn)
        
        self.window.setContentView_(content_view)
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        
        log.info("Preferences window opened")


def show_preferences(app_instance):
    """Show the preferences window."""
    global _preferences_window
    _preferences_window = PreferencesWindow(app_instance)
    _preferences_window.show()
