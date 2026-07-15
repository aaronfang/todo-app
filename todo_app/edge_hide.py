"""Small, dependency-free edge auto-hide controller for Tk windows."""

from __future__ import annotations

import tkinter as tk
import ctypes
import sys
from ctypes.util import find_library
from typing import Callable, Optional


ScreenBounds = tuple[int, int, int, int]


def macos_screen_bounds() -> list[ScreenBounds]:
    """Return all active macOS displays in the coordinate system used by Tk."""
    if sys.platform != "darwin":
        return []

    class CGPoint(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

    class CGSize(ctypes.Structure):
        _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]

    class CGRect(ctypes.Structure):
        _fields_ = [("origin", CGPoint), ("size", CGSize)]

    try:
        framework = find_library("CoreGraphics") or (
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        core_graphics = ctypes.CDLL(framework)
        core_graphics.CGGetActiveDisplayList.argtypes = [
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        core_graphics.CGGetActiveDisplayList.restype = ctypes.c_int32
        core_graphics.CGDisplayBounds.argtypes = [ctypes.c_uint32]
        core_graphics.CGDisplayBounds.restype = CGRect

        count = ctypes.c_uint32()
        if core_graphics.CGGetActiveDisplayList(0, None, ctypes.byref(count)) != 0:
            return []
        display_ids = (ctypes.c_uint32 * count.value)()
        if core_graphics.CGGetActiveDisplayList(
            count.value, display_ids, ctypes.byref(count)
        ) != 0:
            return []

        result = []
        for display_id in display_ids[:count.value]:
            frame = core_graphics.CGDisplayBounds(display_id)
            left = round(frame.origin.x)
            top = round(frame.origin.y)
            result.append((
                left,
                top,
                left + round(frame.size.width),
                top + round(frame.size.height),
            ))
        return result
    except (AttributeError, OSError, TypeError):
        return []


class EdgeHideController:
    """Hide a window beyond the left/right screen edge after the pointer leaves.

    The controller deliberately ignores the top edge on macOS, where the menu bar,
    notch safe area, and full-screen controls make auto-hiding surprising.
    """

    EDGE_THRESHOLD = 12
    REVEAL_STRIP = 8
    HIDE_DELAY_MS = 650
    ANIMATION_STEP_MS = 12
    ANIMATION_STEPS = 10

    def __init__(
        self,
        root: tk.Tk,
        enabled: bool = True,
        on_change: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self.root = root
        self.enabled = enabled
        self.on_change = on_change
        self.edge: Optional[str] = None
        self.hidden = False
        self.animating = False
        self._hide_job: Optional[str] = None
        self._animation_job: Optional[str] = None
        self._visible_geometry = ""
        self._active_bounds: Optional[ScreenBounds] = None
        self._poll_job: Optional[str] = None

        root.bind("<Configure>", self._on_configure, add="+")
        root.bind("<Enter>", self._on_enter, add="+")
        root.bind("<Leave>", self._on_leave, add="+")
        root.bind("<FocusOut>", self._on_leave, add="+")
        self._poll_job = root.after(250, self._poll_pointer)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        self._cancel_hide()
        if not self.enabled:
            self.reveal(animate=False)
            self.edge = None
        if self.on_change:
            self.on_change(self.enabled)

    def toggle(self) -> None:
        self.set_enabled(not self.enabled)

    def geometry_for_save(self) -> str:
        """Return the last usable geometry, never the off-screen hidden geometry."""
        return self._visible_geometry or self.root.geometry()

    def reveal(self, animate: bool = True) -> None:
        self._cancel_hide()
        if not self.hidden or not self.edge:
            return
        target_x = self._visible_x_for_edge(self.edge)
        if animate:
            self._animate_to(target_x, hiding=False)
        else:
            self._set_x(target_x)
            self.hidden = False
            self._remember_visible_geometry()

    def hide(self) -> None:
        self._hide_job = None
        if not self.enabled or self.hidden or self.animating or not self.edge:
            return
        self.root.update_idletasks()
        bounds = self._current_screen_bounds()
        width = self.root.winfo_width()
        target_x = self.hidden_x(self.edge, bounds, width)
        self._animate_to(target_x, hiding=True)

    def _on_configure(self, event: tk.Event) -> None:
        if event.widget is not self.root or not self.enabled or self.hidden or self.animating:
            return
        self._remember_visible_geometry()
        self._update_edge()

    def _update_edge(self) -> None:
        bounds = self._screen_bounds_for_window()
        left, _top, right, _bottom = bounds
        x = self.root.winfo_x()
        window_right = x + self.root.winfo_width()
        if abs(x - left) <= self.EDGE_THRESHOLD:
            self.edge = "left"
            self._active_bounds = bounds
        elif abs(window_right - right) <= self.EDGE_THRESHOLD:
            self.edge = "right"
            self._active_bounds = bounds
        else:
            self.edge = None
            self._active_bounds = None
            self._cancel_hide()

    def _poll_pointer(self) -> None:
        self._poll_job = None
        try:
            if self.enabled and not self.hidden and not self.animating:
                self._update_edge()
                if self.edge and not self._pointer_is_inside_window():
                    if self._hide_job is None:
                        self._hide_job = self.root.after(self.HIDE_DELAY_MS, self.hide)
                elif self._pointer_is_inside_window():
                    self._cancel_hide()
            self._poll_job = self.root.after(250, self._poll_pointer)
        except tk.TclError:
            # The window is already being destroyed.
            self._poll_job = None

    def _pointer_is_inside_window(self) -> bool:
        pointer_x, pointer_y = self.root.winfo_pointerxy()
        x, y = self.root.winfo_x(), self.root.winfo_y()
        return (
            x <= pointer_x < x + self.root.winfo_width()
            and y <= pointer_y < y + self.root.winfo_height()
        )

    def _on_enter(self, _event: tk.Event) -> None:
        self._cancel_hide()
        if self.hidden:
            self.reveal()

    def _on_leave(self, _event: tk.Event) -> None:
        if self.enabled and self.edge and not self.hidden and not self.animating:
            self._cancel_hide()
            self._hide_job = self.root.after(self.HIDE_DELAY_MS, self.hide)

    def _animate_to(self, target_x: int, hiding: bool) -> None:
        self._cancel_animation()
        start_x = self.root.winfo_x()
        delta = target_x - start_x
        if delta == 0:
            self.hidden = hiding
            return
        self.animating = True

        def step(index: int) -> None:
            # Ease out: quick start, gentle landing.
            progress = 1 - (1 - index / self.ANIMATION_STEPS) ** 3
            self._set_x(round(start_x + delta * progress))
            if index < self.ANIMATION_STEPS:
                self._animation_job = self.root.after(
                    self.ANIMATION_STEP_MS, lambda: step(index + 1)
                )
            else:
                self.animating = False
                self.hidden = hiding
                self._animation_job = None
                if not hiding:
                    self._remember_visible_geometry()

        step(1)

    def _visible_x_for_edge(self, edge: str) -> int:
        left, _top, right, _bottom = self._current_screen_bounds()
        return left if edge == "left" else right - self.root.winfo_width()

    def _current_screen_bounds(self) -> ScreenBounds:
        return self._active_bounds or self._screen_bounds_for_window()

    @classmethod
    def hidden_x(cls, edge: str, bounds: ScreenBounds, width: int) -> int:
        left, _top, right, _bottom = bounds
        return left - width + cls.REVEAL_STRIP if edge == "left" else right - cls.REVEAL_STRIP

    def _screen_bounds_for_window(self) -> ScreenBounds:
        screens = macos_screen_bounds()
        if not screens:
            screens = [(0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())]
        return self.select_screen_for_window(
            screens,
            self.root.winfo_x(),
            self.root.winfo_y(),
            self.root.winfo_width(),
            self.root.winfo_height(),
        )

    @staticmethod
    def select_screen_for_window(
        screens: list[ScreenBounds], x: int, y: int, width: int, height: int
    ) -> ScreenBounds:
        """Choose the display containing the largest part of the window."""
        def overlap_area(screen: ScreenBounds) -> int:
            left, top, right, bottom = screen
            overlap_width = max(0, min(x + width, right) - max(x, left))
            overlap_height = max(0, min(y + height, bottom) - max(y, top))
            return overlap_width * overlap_height

        return max(screens, key=overlap_area)

    def _set_x(self, x: int) -> None:
        y = self.root.winfo_y()
        # The explicit leading '+' makes Tk interpret a negative value as an
        # absolute coordinate ("+-392"), rather than a right-edge offset.
        x_spec = f"+{x}"
        y_spec = f"+{y}"
        self.root.geometry(f"{x_spec}{y_spec}")

    def _remember_visible_geometry(self) -> None:
        self._visible_geometry = self.root.geometry()

    def _cancel_hide(self) -> None:
        if self._hide_job is not None:
            self.root.after_cancel(self._hide_job)
            self._hide_job = None

    def _cancel_animation(self) -> None:
        if self._animation_job is not None:
            self.root.after_cancel(self._animation_job)
            self._animation_job = None
