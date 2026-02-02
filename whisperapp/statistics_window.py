"""
Statistics window for WhisperApp.
Modern macOS UI with vibrancy effects displaying usage stats.
"""
import logging
from typing import Dict

log = logging.getLogger(__name__)

_stats_window = None


class StatisticsWindow:
    """Native macOS statistics window with modern styling."""
    
    def __init__(self, stats: Dict):
        self.stats = stats
        self.window = None
    
    def show(self):
        """Show the statistics window."""
        try:
            self._create_window()
        except Exception as e:
            log.error(f"Failed to show statistics: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_window(self):
        """Create the statistics window with modern styling."""
        from AppKit import (
            NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
            NSWindowStyleMaskFullSizeContentView, NSBackingStoreBuffered,
            NSScreen, NSView, NSMakeRect, NSTextField, NSFont, NSColor, NSApp,
            NSVisualEffectView, NSVisualEffectBlendingModeBehindWindow,
            NSVisualEffectMaterialHUDWindow, NSVisualEffectStateActive, NSBox
        )
        
        stats = self.stats
        
        # Window dimensions
        win_width = 380
        win_height = 340
        
        # Center on screen
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        x = (screen_frame.size.width - win_width) / 2
        y = (screen_frame.size.height - win_height) / 2
        
        frame = ((x, y), (win_width, win_height))
        
        # Create window
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
        self.window.setTitle_("Statistics")
        self.window.setTitlebarAppearsTransparent_(True)
        self.window.setTitleVisibility_(1)
        
        # Vibrancy background
        vibrancy_view = NSVisualEffectView.alloc().initWithFrame_(((0, 0), (win_width, win_height)))
        vibrancy_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
        vibrancy_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        vibrancy_view.setState_(NSVisualEffectStateActive)
        
        y_pos = win_height - 50
        
        # Header
        header_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, y_pos, win_width, 28))
        header_label.setStringValue_("Statistics")
        header_label.setFont_(NSFont.boldSystemFontOfSize_(22))
        header_label.setTextColor_(NSColor.labelColor())
        header_label.setBezeled_(False)
        header_label.setDrawsBackground_(False)
        header_label.setEditable_(False)
        header_label.setAlignment_(1)
        vibrancy_view.addSubview_(header_label)
        
        y_pos -= 40
        
        # All Time Stats Card
        card_margin = 20
        card_width = win_width - (card_margin * 2)
        
        self._add_stat_card(vibrancy_view, "All Time", [
            ("Transcriptions", f"{stats['total_transcriptions']:,}"),
            ("Words Typed", f"{stats['total_words']:,}"),
            ("Recording Time", f"{stats['total_minutes']:.1f} min"),
            ("Avg Speed", f"{stats['avg_wpm']:.0f} WPM"),
        ], card_margin, y_pos - 105, card_width, 115)
        
        y_pos -= 140
        
        # Today Stats Card
        self._add_stat_card(vibrancy_view, "Today", [
            ("Transcriptions", f"{stats['today_count']:,}"),
            ("Words Typed", f"{stats['today_words']:,}"),
        ], card_margin, y_pos - 65, card_width, 75)
        
        self.window.setContentView_(vibrancy_view)
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        
        log.info("Statistics window opened")
    
    def _add_stat_card(self, parent_view, title, stats_list, x, y, width, height):
        """Add a statistics card with title and key-value pairs."""
        from AppKit import (
            NSVisualEffectView, NSVisualEffectStateActive,
            NSTextField, NSFont, NSColor, NSMakeRect
        )
        
        card = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
        card.setMaterial_(3)
        card.setBlendingMode_(0)
        card.setState_(NSVisualEffectStateActive)
        card.setWantsLayer_(True)
        card.layer().setCornerRadius_(12)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(0.5)
        card.layer().setBorderColor_(NSColor.separatorColor().CGColor())
        
        # Card title
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(15, height - 28, width - 30, 20))
        title_label.setStringValue_(title)
        title_label.setFont_(NSFont.boldSystemFontOfSize_(12))
        title_label.setTextColor_(NSColor.secondaryLabelColor())
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        card.addSubview_(title_label)
        
        # Stats rows
        row_y = height - 50
        for label, value in stats_list:
            # Label
            label_field = NSTextField.alloc().initWithFrame_(NSMakeRect(15, row_y, 120, 18))
            label_field.setStringValue_(label)
            label_field.setFont_(NSFont.systemFontOfSize_(13))
            label_field.setTextColor_(NSColor.labelColor())
            label_field.setBezeled_(False)
            label_field.setDrawsBackground_(False)
            label_field.setEditable_(False)
            card.addSubview_(label_field)
            
            # Value
            value_field = NSTextField.alloc().initWithFrame_(NSMakeRect(140, row_y, width - 160, 18))
            value_field.setStringValue_(value)
            value_field.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(13, 0.5))
            value_field.setTextColor_(NSColor.labelColor())
            value_field.setBezeled_(False)
            value_field.setDrawsBackground_(False)
            value_field.setEditable_(False)
            value_field.setAlignment_(2)  # Right align
            card.addSubview_(value_field)
            
            row_y -= 20
        
        parent_view.addSubview_(card)


def show_statistics_window(stats: Dict):
    """Show the statistics window."""
    global _stats_window
    _stats_window = StatisticsWindow(stats)
    _stats_window.show()
