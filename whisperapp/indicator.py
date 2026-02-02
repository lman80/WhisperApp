"""
Recording indicator - polished floating pill with audio visualization.
Shows a modern, glowing indicator when recording.
"""
import threading
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Indicator state
_indicator = None


class RecordingIndicator:
    """Polished floating recording indicator."""
    
    def __init__(self):
        self.window = None
        self.view = None
        self.is_visible = False
        self.current_level = 0.0
        self._update_thread = None
        self._initialized = False
        
    def _init_window(self):
        """Initialize the NSWindow (must be called on main thread)."""
        if self._initialized:
            return
            
        try:
            from AppKit import (
                NSWindow, NSView, NSColor, NSBezierPath,
                NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
                NSFloatingWindowLevel, NSScreen, NSFont,
                NSFontAttributeName, NSForegroundColorAttributeName,
                NSMutableParagraphStyle, NSParagraphStyleAttributeName,
                NSCenterTextAlignment
            )
            from Foundation import NSString, NSDictionary, NSMakeRect
            import objc
            
            # Window dimensions - pill shape (wider for 5 bars)
            win_width = 95
            win_height = 36
            
            # Create a custom view for the polished indicator
            class PolishedIndicatorView(NSView):
                level = objc.ivar('level', objc._C_FLT)
                pulse_phase = objc.ivar('pulse_phase', objc._C_FLT)
                
                def initWithFrame_(self, frame):
                    self = objc.super(PolishedIndicatorView, self).initWithFrame_(frame)
                    if self:
                        self.level = 0.0
                        self.pulse_phase = 0.0
                    return self
                
                def drawRect_(self, rect):
                    # Clear background
                    NSColor.clearColor().set()
                    NSBezierPath.fillRect_(rect)
                    
                    w = rect.size.width
                    h = rect.size.height
                    padding = 2
                    
                    # Calculate pulse effect
                    import math
                    pulse = 0.5 + 0.5 * math.sin(self.pulse_phase)
                    glow_intensity = 0.3 + (self.level * 0.5) + (pulse * 0.2)
                    
                    # Outer glow (soft red)
                    glow_rect = NSMakeRect(padding - 3, padding - 3, w - padding*2 + 6, h - padding*2 + 6)
                    glow_color = NSColor.colorWithRed_green_blue_alpha_(1.0, 0.2, 0.2, glow_intensity * 0.5)
                    glow_color.set()
                    glow_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(glow_rect, h/2, h/2)
                    glow_path.fill()
                    
                    # Main pill background (dark with transparency)
                    pill_rect = NSMakeRect(padding, padding, w - padding*2, h - padding*2)
                    bg_color = NSColor.colorWithRed_green_blue_alpha_(0.1, 0.1, 0.12, 0.95)
                    bg_color.set()
                    pill_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pill_rect, (h - padding*2)/2, (h - padding*2)/2)
                    pill_path.fill()
                    
                    # Subtle border
                    border_color = NSColor.colorWithRed_green_blue_alpha_(1.0, 0.3, 0.3, 0.4 + self.level * 0.3)
                    border_color.set()
                    pill_path.setLineWidth_(1.5)
                    pill_path.stroke()
                    
                    # Red recording dot (pulsing)
                    dot_size = 10 + (self.level * 4) + (pulse * 2)
                    dot_x = 16
                    dot_y = h / 2
                    dot_rect = NSMakeRect(dot_x - dot_size/2, dot_y - dot_size/2, dot_size, dot_size)
                    
                    # Dot glow
                    dot_glow_size = dot_size + 6
                    dot_glow_rect = NSMakeRect(dot_x - dot_glow_size/2, dot_y - dot_glow_size/2, dot_glow_size, dot_glow_size)
                    dot_glow_color = NSColor.colorWithRed_green_blue_alpha_(1.0, 0.2, 0.2, 0.4)
                    dot_glow_color.set()
                    NSBezierPath.bezierPathWithOvalInRect_(dot_glow_rect).fill()
                    
                    # Main dot with gradient effect (simulated with layered circles)
                    # Outer ring
                    dot_color = NSColor.colorWithRed_green_blue_alpha_(1.0, 0.25, 0.25, 1.0)
                    dot_color.set()
                    NSBezierPath.bezierPathWithOvalInRect_(dot_rect).fill()
                    
                    # Inner highlight
                    inner_size = dot_size * 0.6
                    inner_rect = NSMakeRect(dot_x - inner_size/2 - 1, dot_y - inner_size/2 + 1, inner_size, inner_size)
                    inner_color = NSColor.colorWithRed_green_blue_alpha_(1.0, 0.5, 0.5, 0.6)
                    inner_color.set()
                    NSBezierPath.bezierPathWithOvalInRect_(inner_rect).fill()
                    
                    # "REC" text
                    text = "REC"
                    font = NSFont.boldSystemFontOfSize_(11)
                    text_color = NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.9)
                    
                    attrs = {
                        NSFontAttributeName: font,
                        NSForegroundColorAttributeName: text_color
                    }
                    
                    ns_text = NSString.stringWithString_(text)
                    text_size = ns_text.sizeWithAttributes_(attrs)
                    text_x = 32
                    text_y = (h - text_size.height) / 2
                    ns_text.drawAtPoint_withAttributes_((text_x, text_y), attrs)
                    
                    # Audio level bars (5 bars for waveform effect)
                    bar_x_start = 56
                    bar_width = 3
                    bar_spacing = 4
                    bar_max_height = 16
                    bar_y = h / 2
                    
                    for i in range(5):
                        # Different heights based on level with wave-like variation
                        import math
                        phase_offset = i * 0.7 + self.pulse_phase
                        bar_level = self.level * (0.6 + 0.4 * math.sin(phase_offset * 4))
                        bar_height = 3 + (bar_level * bar_max_height)
                        
                        bar_rect = NSMakeRect(
                            bar_x_start + i * bar_spacing,
                            bar_y - bar_height / 2,
                            bar_width,
                            bar_height
                        )
                        
                        # Bar color (white with level-based opacity)
                        bar_alpha = 0.4 + bar_level * 0.6
                        bar_color = NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, bar_alpha)
                        bar_color.set()
                        
                        bar_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bar_rect, 1.5, 1.5)
                        bar_path.fill()
            
            # Position at bottom center of screen
            screen = NSScreen.mainScreen()
            screen_frame = screen.frame()
            x = (screen_frame.size.width - win_width) / 2
            y = 80  # 80px from bottom of screen
            
            frame = ((x, y), (win_width, win_height))
            
            self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                frame,
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False
            )
            
            # Make it floating and transparent
            self.window.setLevel_(NSFloatingWindowLevel + 100)  # Very high level
            self.window.setOpaque_(False)
            self.window.setBackgroundColor_(NSColor.clearColor())
            self.window.setIgnoresMouseEvents_(True)
            self.window.setHasShadow_(True)
            self.window.setCollectionBehavior_(1 << 0)  # NSWindowCollectionBehaviorCanJoinAllSpaces
            
            # Create and set the view
            self.view = PolishedIndicatorView.alloc().initWithFrame_(((0, 0), (win_width, win_height)))
            self.window.setContentView_(self.view)
            
            self._initialized = True
            log.debug("Polished recording indicator initialized")
            
        except Exception as e:
            log.error(f"Failed to initialize indicator: {e}")
            import traceback
            traceback.print_exc()
    
    def show(self):
        """Show the indicator."""
        def _show():
            self._init_window()
            if self.window:
                self.window.orderFront_(None)
                self.is_visible = True
                self._start_animation()
                log.debug("Recording indicator shown")
        
        self._run_on_main(_show)
    
    def hide(self):
        """Hide the indicator."""
        def _hide():
            self.is_visible = False
            if self.window:
                self.window.orderOut_(None)
                log.debug("Recording indicator hidden")
        
        self._run_on_main(_hide)
    
    def update_level(self, level: float):
        """Update the audio level (0.0 to 1.0)."""
        # Amplify level 10x for better responsiveness
        self.current_level = min(1.0, max(0.0, level * 10))
    
    def _start_animation(self):
        """Start the animation loop for smooth pulsing."""
        def animate():
            import time
            phase = 0.0
            while self.is_visible:
                phase += 0.15
                
                def _update(p=phase, l=self.current_level):
                    if self.view:
                        self.view.level = l
                        self.view.pulse_phase = p
                        self.view.setNeedsDisplay_(True)
                
                self._run_on_main(_update)
                time.sleep(0.033)  # ~30 FPS
        
        self._update_thread = threading.Thread(target=animate, daemon=True)
        self._update_thread.start()
    
    def _run_on_main(self, func):
        """Run function on main thread."""
        try:
            from PyObjCTools import AppHelper
            AppHelper.callAfter(func)
        except:
            func()


def get_indicator() -> RecordingIndicator:
    """Get or create the singleton indicator."""
    global _indicator
    if _indicator is None:
        _indicator = RecordingIndicator()
    return _indicator


def show_indicator():
    """Show the recording indicator."""
    get_indicator().show()


def hide_indicator():
    """Hide the recording indicator."""
    get_indicator().hide()


def update_indicator_level(level: float):
    """Update the audio level on the indicator."""
    get_indicator().update_level(level)
