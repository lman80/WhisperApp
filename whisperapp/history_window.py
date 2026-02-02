"""
History window for WhisperApp.
Scrollable list of past transcriptions with copy functionality.
"""
import logging
from typing import Optional

log = logging.getLogger(__name__)

_history_window = None


class HistoryWindow:
    """Native macOS window showing transcription history."""
    
    def __init__(self, database):
        self.db = database
        self.window = None
        self.table_view = None
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
        """Create the native macOS window."""
        from AppKit import (
            NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
            NSWindowStyleMaskResizable, NSBackingStoreBuffered, NSScreen,
            NSScrollView, NSTableView, NSTableColumn, NSColor,
            NSFont, NSView, NSMakeRect, NSTextField, NSButton,
            NSBezelStyleRounded, NSTextFieldCell, NSApp,
            NSWindowStyleMaskMiniaturizable
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
        win_width = 600
        win_height = 500
        
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
            NSWindowStyleMaskResizable |
            NSWindowStyleMaskMiniaturizable
        )
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_("WhisperApp History")
        self.window.setMinSize_((400, 300))
        
        # Create content view
        content_frame = ((0, 0), (win_width, win_height))
        content_view = NSView.alloc().initWithFrame_(content_frame)
        
        # Dark background
        content_view.setWantsLayer_(True)
        content_view.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.1, 0.1, 0.1, 1.0).CGColor())
        
        # Create scroll view with text items
        scroll_rect = NSMakeRect(10, 50, win_width - 20, win_height - 60)
        scroll_view = NSScrollView.alloc().initWithFrame_(scroll_rect)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(2 | 16)  # Resize with window
        
        # Create container for history items
        item_height = 70
        total_height = max(len(self.history_data) * item_height, win_height - 60)
        doc_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, win_width - 40, total_height))
        
        # Add history items (newest first, from top)
        for i, item in enumerate(self.history_data):
            y_pos = total_height - (i + 1) * item_height
            item_frame = NSMakeRect(0, y_pos, win_width - 40, item_height - 5)
            
            # Create item view
            item_view = NSView.alloc().initWithFrame_(item_frame)
            item_view.setWantsLayer_(True)
            item_view.layer().setBackgroundColor_(
                NSColor.colorWithRed_green_blue_alpha_(0.15, 0.15, 0.15, 1.0).CGColor()
            )
            item_view.layer().setCornerRadius_(8)
            
            # Timestamp label
            timestamp = item['created_at'][:16].replace('T', ' ')
            duration = item.get('duration', 0) or 0
            header_text = f"{timestamp}  •  {duration:.1f}s"
            
            header_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, item_height - 30, 300, 18))
            header_label.setStringValue_(header_text)
            header_label.setFont_(NSFont.systemFontOfSize_(11))
            header_label.setTextColor_(NSColor.grayColor())
            header_label.setBezeled_(False)
            header_label.setDrawsBackground_(False)
            header_label.setEditable_(False)
            header_label.setSelectable_(False)
            item_view.addSubview_(header_label)
            
            # Text content (truncated)
            text = item['text']
            if len(text) > 100:
                text = text[:100] + "..."
            
            text_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 8, win_width - 130, 35))
            text_label.setStringValue_(text)
            text_label.setFont_(NSFont.systemFontOfSize_(13))
            text_label.setTextColor_(NSColor.whiteColor())
            text_label.setBezeled_(False)
            text_label.setDrawsBackground_(False)
            text_label.setEditable_(False)
            text_label.setSelectable_(True)  # Allow text selection
            item_view.addSubview_(text_label)
            
            # Copy button
            copy_btn = NSButton.alloc().initWithFrame_(NSMakeRect(win_width - 110, 15, 60, 30))
            copy_btn.setTitle_("Copy")
            copy_btn.setBezelStyle_(NSBezelStyleRounded)
            copy_btn.setFont_(NSFont.systemFontOfSize_(11))
            
            # Store the full text for copying
            full_text = item['text']
            
            # Create a callback that captures the text
            def make_copy_action(text_to_copy):
                def copy_action(sender):
                    pyperclip.copy(text_to_copy)
                    sender.setTitle_("✓")
                    # Reset title after delay
                    def reset():
                        sender.setTitle_("Copy")
                    from threading import Timer
                    Timer(1.0, reset).start()
                return copy_action
            
            copy_btn.setTarget_(copy_btn)
            copy_btn.setAction_(objc.selector(make_copy_action(full_text), signature=b'v@:@'))
            item_view.addSubview_(copy_btn)
            
            doc_view.addSubview_(item_view)
        
        scroll_view.setDocumentView_(doc_view)
        content_view.addSubview_(scroll_view)
        
        # Close button at bottom
        close_btn = NSButton.alloc().initWithFrame_(NSMakeRect(win_width - 90, 10, 80, 30))
        close_btn.setTitle_("Close")
        close_btn.setBezelStyle_(NSBezelStyleRounded)
        close_btn.setTarget_(self.window)
        close_btn.setAction_(objc.selector(self.window.close, signature=b'v@:'))
        content_view.addSubview_(close_btn)
        
        self.window.setContentView_(content_view)
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        
        log.info(f"History window opened with {len(self.history_data)} items")


def show_history_window(database):
    """Show the history window."""
    global _history_window
    _history_window = HistoryWindow(database)
    _history_window.show()
