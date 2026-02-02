"""
Preferences window for WhisperApp.
Modern macOS UI with vibrancy effects and native styling.
"""
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_preferences_window = None


class PreferencesWindow:
    """Native macOS preferences window with modern vibrancy effects."""
    
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
        """Create the native preferences window with modern styling."""
        from AppKit import (
            NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
            NSWindowStyleMaskFullSizeContentView, NSBackingStoreBuffered,
            NSScreen, NSView, NSMakeRect, NSTextField, NSButton, 
            NSPopUpButton, NSFont, NSColor, NSApp, NSBox,
            NSImage, NSImageView, NSOnState, NSOffState,
            NSVisualEffectView, NSVisualEffectBlendingModeBehindWindow,
            NSVisualEffectMaterialHUDWindow, NSVisualEffectStateActive
        )
        import objc
        
        # Window dimensions
        win_width = 420
        win_height = 400
        
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
        
        y_pos = win_height - 50
        
        # === App Header with Icon ===
        assets_dir = Path(__file__).parent / "assets"
        icon_path = assets_dir / "AppIcon.png"
        
        # Center header section
        header_x = (win_width - 200) / 2
        
        if icon_path.exists():
            image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if image:
                image.setSize_((72, 72))
                image_view = NSImageView.alloc().initWithFrame_(NSMakeRect((win_width - 72) / 2, y_pos - 30, 72, 72))
                image_view.setImage_(image)
                vibrancy_view.addSubview_(image_view)
        
        y_pos -= 95
        
        # App name - centered
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, y_pos, win_width, 28))
        title_label.setStringValue_("WhisperApp")
        title_label.setFont_(NSFont.boldSystemFontOfSize_(22))
        title_label.setTextColor_(NSColor.labelColor())
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setAlignment_(1)  # Center
        vibrancy_view.addSubview_(title_label)
        
        y_pos -= 22
        
        # Version - centered
        version_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, y_pos, win_width, 18))
        version_label.setStringValue_("Version 1.0.0")
        version_label.setFont_(NSFont.systemFontOfSize_(12))
        version_label.setTextColor_(NSColor.secondaryLabelColor())
        version_label.setBezeled_(False)
        version_label.setDrawsBackground_(False)
        version_label.setEditable_(False)
        version_label.setAlignment_(1)  # Center
        vibrancy_view.addSubview_(version_label)
        
        y_pos -= 35
        
        # === Settings Card ===
        card_margin = 20
        card_width = win_width - (card_margin * 2)
        card_height = 160
        
        card = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(card_margin, y_pos - card_height + 20, card_width, card_height))
        card.setMaterial_(3)
        card.setBlendingMode_(0)
        card.setState_(NSVisualEffectStateActive)
        card.setWantsLayer_(True)
        card.layer().setCornerRadius_(12)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(0.5)
        card.layer().setBorderColor_(NSColor.separatorColor().CGColor())
        
        inner_y = card_height - 35
        
        # Model selection row
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(15, inner_y, 80, 20))
        model_label.setStringValue_("Model")
        model_label.setFont_(NSFont.systemFontOfSize_(13))
        model_label.setTextColor_(NSColor.labelColor())
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        card.addSubview_(model_label)
        
        from .models import AVAILABLE_MODELS, is_model_downloaded
        
        model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(100, inner_y - 3, card_width - 120, 26))
        model_popup.removeAllItems()
        
        for key, info in AVAILABLE_MODELS.items():
            downloaded = is_model_downloaded(key)
            prefix = "✓ " if downloaded else "↓ "
            model_popup.addItemWithTitle_(f"{prefix}{info.name}")
            if key == self.app.current_model:
                model_popup.selectItemWithTitle_(f"{prefix}{info.name}")
        
        card.addSubview_(model_popup)
        
        inner_y -= 45
        
        # Separator
        sep = NSBox.alloc().initWithFrame_(NSMakeRect(15, inner_y + 10, card_width - 30, 1))
        sep.setBoxType_(2)
        card.addSubview_(sep)
        
        inner_y -= 10
        
        # Cleanup toggle row
        cleanup_label = NSTextField.alloc().initWithFrame_(NSMakeRect(15, inner_y, 120, 20))
        cleanup_label.setStringValue_("AI Formatting")
        cleanup_label.setFont_(NSFont.systemFontOfSize_(13))
        cleanup_label.setTextColor_(NSColor.labelColor())
        cleanup_label.setBezeled_(False)
        cleanup_label.setDrawsBackground_(False)
        cleanup_label.setEditable_(False)
        card.addSubview_(cleanup_label)
        
        cleanup_btn = NSButton.alloc().initWithFrame_(NSMakeRect(card_width - 65, inner_y - 2, 50, 24))
        cleanup_btn.setButtonType_(13)  # Switch style
        cleanup_btn.setTitle_("")
        cleanup_btn.setState_(NSOnState if self.app.cleanup_enabled else NSOffState)
        
        def toggle_cleanup(sender):
            self.app.cleanup_enabled = (sender.state() == NSOnState)
        
        cleanup_btn.setTarget_(cleanup_btn)
        cleanup_btn.setAction_(objc.selector(toggle_cleanup, signature=b'v@:@'))
        card.addSubview_(cleanup_btn)
        
        inner_y -= 45
        
        # Separator
        sep2 = NSBox.alloc().initWithFrame_(NSMakeRect(15, inner_y + 10, card_width - 30, 1))
        sep2.setBoxType_(2)
        card.addSubview_(sep2)
        
        inner_y -= 10
        
        # Hotkey display row
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(15, inner_y, 80, 20))
        hotkey_label.setStringValue_("Hotkey")
        hotkey_label.setFont_(NSFont.systemFontOfSize_(13))
        hotkey_label.setTextColor_(NSColor.labelColor())
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        card.addSubview_(hotkey_label)
        
        hotkey_value = NSTextField.alloc().initWithFrame_(NSMakeRect(100, inner_y, card_width - 120, 20))
        hotkey_value.setStringValue_("Hold Right ⌘")
        hotkey_value.setFont_(NSFont.systemFontOfSize_(13))
        hotkey_value.setTextColor_(NSColor.secondaryLabelColor())
        hotkey_value.setBezeled_(False)
        hotkey_value.setDrawsBackground_(False)
        hotkey_value.setEditable_(False)
        hotkey_value.setAlignment_(2)  # Right align
        card.addSubview_(hotkey_value)
        
        vibrancy_view.addSubview_(card)
        
        # === Footer text ===
        footer_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 25, win_width, 16))
        footer_label.setStringValue_("Local AI • No data leaves your Mac")
        footer_label.setFont_(NSFont.systemFontOfSize_(11))
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


def show_preferences(app_instance):
    """Show the preferences window."""
    global _preferences_window
    _preferences_window = PreferencesWindow(app_instance)
    _preferences_window.show()
