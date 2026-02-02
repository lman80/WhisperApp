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
        
        model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(80, model_card_height - 40, card_width - 100, 26))
        model_popup.removeAllItems()
        
        for key, info in AVAILABLE_MODELS.items():
            downloaded = is_model_downloaded(key)
            prefix = "✓ " if downloaded else "↓ "
            model_popup.addItemWithTitle_(f"{prefix}{info.name}")
            if key == self.app.current_model:
                model_popup.selectItemWithTitle_(f"{prefix}{info.name}")
        
        model_card.addSubview_(model_popup)
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
        
        hotkey_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(90, hotkey_card_height - 40, card_width - 110, 26))
        hotkey_popup.removeAllItems()
        
        current_key = self.app.hotkey_manager.trigger_key_name if self.app.hotkey_manager else 'cmd_r'
        
        for key_name, display in HotkeyManager.KEY_DISPLAY.items():
            hotkey_popup.addItemWithTitle_(display)
            if key_name == current_key:
                hotkey_popup.selectItemWithTitle_(display)
        
        # Create callback for hotkey change
        def on_hotkey_change(sender):
            selected = sender.titleOfSelectedItem()
            # Find the key name
            for key_name, display in HotkeyManager.KEY_DISPLAY.items():
                if display == selected:
                    if self.app.hotkey_manager:
                        self.app.hotkey_manager.set_trigger_key(key_name)
                    break
        
        hotkey_popup.setTarget_(hotkey_popup)
        hotkey_popup.setAction_(objc.selector(on_hotkey_change, signature=b'v@:@'))
        hotkey_card.addSubview_(hotkey_popup)
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
        
        cleanup_btn = NSButton.alloc().initWithFrame_(NSMakeRect(card_width - 60, format_card_height - 40, 50, 26))
        cleanup_btn.setButtonType_(13)  # Switch style
        cleanup_btn.setTitle_("")
        cleanup_btn.setState_(NSOnState if self.app.cleanup_enabled else NSOffState)
        
        def toggle_cleanup(sender):
            self.app.cleanup_enabled = (sender.state() == NSOnState)
        
        cleanup_btn.setTarget_(cleanup_btn)
        cleanup_btn.setAction_(objc.selector(toggle_cleanup, signature=b'v@:@'))
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
