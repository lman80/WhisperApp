"""
History window for WhisperApp.
Modern macOS UI with vibrancy, blur effects, and native styling.
"""
import logging
from typing import Optional

log = logging.getLogger(__name__)

_history_window = None


class HistoryWindow:
    """Native macOS window with modern vibrancy effects."""
    
    def __init__(self, database):
        self.db = database
        self.window = None
        self.history_data = []
    
    def show(self):
        """Show the history window."""
        try:
            self._create_window()
        except Exception as e:
            log.error(f"Failed to show history window: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_window(self):
        """Create the native macOS window with modern styling."""
        from AppKit import (
            NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
            NSWindowStyleMaskResizable, NSWindowStyleMaskFullSizeContentView,
            NSBackingStoreBuffered, NSScreen, NSScrollView, NSColor,
            NSFont, NSView, NSMakeRect, NSTextField, NSButton,
            NSApp, NSWindowStyleMaskMiniaturizable,
            NSVisualEffectView, NSVisualEffectBlendingModeBehindWindow,
            NSVisualEffectMaterialHUDWindow, NSVisualEffectStateActive,
            NSTableView, NSTableColumn, NSBox
        )
        from PyObjCTools import AppHelper
        import objc
        import pyperclip
        
        # Load history
        self.history_data = self.db.get_transcriptions(limit=100)
        
        if not self.history_data:
            import rumps
            rumps.alert(
                title="Transcription History",
                message="No transcriptions yet!\n\nHold Right ⌘ and speak to transcribe.",
                ok="OK"
            )
            return
        
        # Window dimensions
        win_width = 650
        win_height = 550
        
        # Center on screen
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        x = (screen_frame.size.width - win_width) / 2
        y = (screen_frame.size.height - win_height) / 2
        
        frame = ((x, y), (win_width, win_height))
        
        # Create window with full size content view for modern look
        style_mask = (
            NSWindowStyleMaskTitled | 
            NSWindowStyleMaskClosable | 
            NSWindowStyleMaskResizable |
            NSWindowStyleMaskMiniaturizable |
            NSWindowStyleMaskFullSizeContentView
        )
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_("History")
        self.window.setMinSize_((450, 350))
        self.window.setTitlebarAppearsTransparent_(True)
        self.window.setTitleVisibility_(1)  # Hidden
        
        # Create vibrancy effect view as background (liquid glass effect)
        content_frame = ((0, 0), (win_width, win_height))
        vibrancy_view = NSVisualEffectView.alloc().initWithFrame_(content_frame)
        vibrancy_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
        vibrancy_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        vibrancy_view.setState_(NSVisualEffectStateActive)
        vibrancy_view.setAutoresizingMask_(2 | 16)  # Resize with window
        
        # Header with title
        header_height = 60
        header_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, win_height - header_height + 15, 200, 28))
        header_label.setStringValue_("Transcription History")
        header_label.setFont_(NSFont.boldSystemFontOfSize_(20))
        header_label.setTextColor_(NSColor.labelColor())
        header_label.setBezeled_(False)
        header_label.setDrawsBackground_(False)
        header_label.setEditable_(False)
        header_label.setSelectable_(False)
        vibrancy_view.addSubview_(header_label)
        
        # Item count badge
        count_label = NSTextField.alloc().initWithFrame_(NSMakeRect(220, win_height - header_height + 18, 100, 20))
        count_label.setStringValue_(f"{len(self.history_data)} items")
        count_label.setFont_(NSFont.systemFontOfSize_(12))
        count_label.setTextColor_(NSColor.secondaryLabelColor())
        count_label.setBezeled_(False)
        count_label.setDrawsBackground_(False)
        count_label.setEditable_(False)
        vibrancy_view.addSubview_(count_label)
        
        # Scroll view for history items
        scroll_rect = NSMakeRect(15, 15, win_width - 30, win_height - header_height - 25)
        scroll_view = NSScrollView.alloc().initWithFrame_(scroll_rect)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(2 | 16)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setBorderType_(0)  # No border
        
        # Container for history items
        item_height = 85
        spacing = 8
        total_height = max(len(self.history_data) * (item_height + spacing), scroll_rect[1][1])
        doc_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, win_width - 50, total_height))
        
        # Add history items with modern card styling
        for i, item in enumerate(self.history_data):
            y_pos = total_height - (i + 1) * (item_height + spacing)
            card_width = win_width - 55
            card_frame = NSMakeRect(0, y_pos, card_width, item_height)
            
            # Card with subtle vibrancy
            card_view = NSVisualEffectView.alloc().initWithFrame_(card_frame)
            card_view.setMaterial_(3)  # Light material
            card_view.setBlendingMode_(0)  # Within window
            card_view.setState_(NSVisualEffectStateActive)
            card_view.setWantsLayer_(True)
            card_view.layer().setCornerRadius_(12)
            card_view.layer().setMasksToBounds_(True)
            
            # Subtle border
            card_view.layer().setBorderWidth_(0.5)
            card_view.layer().setBorderColor_(NSColor.separatorColor().CGColor())
            
            # Timestamp and duration header
            timestamp = item['created_at'][:16].replace('T', ' ')
            duration = item.get('duration', 0) or 0
            word_count = len(item['text'].split())
            header_text = f"{timestamp}  •  {duration:.1f}s  •  {word_count} words"
            
            meta_label = NSTextField.alloc().initWithFrame_(NSMakeRect(15, item_height - 28, card_width - 90, 18))
            meta_label.setStringValue_(header_text)
            meta_label.setFont_(NSFont.systemFontOfSize_(11))
            meta_label.setTextColor_(NSColor.secondaryLabelColor())
            meta_label.setBezeled_(False)
            meta_label.setDrawsBackground_(False)
            meta_label.setEditable_(False)
            meta_label.setSelectable_(False)
            card_view.addSubview_(meta_label)
            
            # Text content (truncated nicely)
            text = item['text']
            max_chars = 120
            if len(text) > max_chars:
                text = text[:max_chars].rsplit(' ', 1)[0] + "…"
            
            text_label = NSTextField.alloc().initWithFrame_(NSMakeRect(15, 12, card_width - 95, 42))
            text_label.setStringValue_(text)
            text_label.setFont_(NSFont.systemFontOfSize_(13))
            text_label.setTextColor_(NSColor.labelColor())
            text_label.setBezeled_(False)
            text_label.setDrawsBackground_(False)
            text_label.setEditable_(False)
            text_label.setSelectable_(True)
            text_label.setLineBreakMode_(4)  # Truncate tail
            card_view.addSubview_(text_label)
            
            # Copy button - modern pill style
            copy_btn = NSButton.alloc().initWithFrame_(NSMakeRect(card_width - 70, 25, 55, 28))
            copy_btn.setTitle_("Copy")
            copy_btn.setBezelStyle_(14)  # Rounded rect / pill
            copy_btn.setFont_(NSFont.systemFontOfSize_(12))
            
            full_text = item['text']
            
            def make_copy_action(text_to_copy):
                def copy_action(sender):
                    pyperclip.copy(text_to_copy)
                    sender.setTitle_("✓")
                    def reset():
                        try:
                            sender.setTitle_("Copy")
                        except:
                            pass
                    from threading import Timer
                    Timer(1.0, reset).start()
                return copy_action
            
            copy_btn.setTarget_(copy_btn)
            copy_btn.setAction_(objc.selector(make_copy_action(full_text), signature=b'v@:@'))
            card_view.addSubview_(copy_btn)
            
            doc_view.addSubview_(card_view)
        
        scroll_view.setDocumentView_(doc_view)
        vibrancy_view.addSubview_(scroll_view)
        
        self.window.setContentView_(vibrancy_view)
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        
        log.info(f"History window opened with {len(self.history_data)} items")


def show_history_window(database):
    """Show the history window."""
    global _history_window
    _history_window = HistoryWindow(database)
    _history_window.show()
