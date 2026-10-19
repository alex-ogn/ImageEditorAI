"""Canvas that displays an image fitted to all available space."""

import tkinter as tk

from PIL import Image, ImageTk

from image_editor_ai.imaging import Box, box_to_canvas, fit_size, fitted_origin
from image_editor_ai.platform_utils import shortcut_label
from image_editor_ai.ui import theme

RESIZE_DEBOUNCE_MS = 50


class ImageView(tk.Canvas):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=theme.CANVAS_BG, highlightthickness=0, borderwidth=0)
        self._original: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None  # keep a reference or Tk drops it
        self._pending_render: str | None = None
        # Detection overlay: box in image fractions plus its label.
        self._detection: tuple[Box, str] | None = None
        self.bind("<Configure>", self._on_configure)

    @property
    def image(self) -> Image.Image | None:
        return self._original

    def set_image(self, image: Image.Image) -> None:
        self._original = image
        self._detection = None
        self._render()

    def set_detection(self, box: Box | None, label: str = "") -> None:
        """Draw (or clear, with None) a box given as image fractions; the image is untouched."""
        self._detection = (box, label) if box is not None else None
        self._render()

    def _on_configure(self, _event: tk.Event) -> None:
        if self._pending_render is not None:
            self.after_cancel(self._pending_render)
        self._pending_render = self.after(RESIZE_DEBOUNCE_MS, self._render)

    def _render(self) -> None:
        self._pending_render = None
        self.delete("all")
        box_w, box_h = self.winfo_width(), self.winfo_height()
        if box_w <= 1 or box_h <= 1:
            return

        if self._original is None:
            self.create_text(
                box_w / 2,
                box_h / 2,
                text=f"Open an image ({shortcut_label('o')})",
                fill=theme.HINT_FG,
                font="TkHeadingFont",
            )
            return

        # Always resize from the untouched original with one uniform scale.
        size = fit_size(*self._original.size, box_w, box_h)
        display = self._original
        if display.mode not in ("RGB", "RGBA"):
            display = display.convert("RGBA")
        display = display.resize(size, Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(display)
        self.create_image(*fitted_origin(*size, box_w, box_h), image=self._photo, anchor=tk.NW)
        self._render_detection(box_w, box_h)

    def _render_detection(self, box_w: int, box_h: int) -> None:
        if self._detection is None or self._original is None:
            return
        box, label = self._detection
        x0, y0, x1, y1 = box_to_canvas(box, *self._original.size, box_w, box_h)
        self.create_rectangle(x0, y0, x1, y1, outline=theme.ACCENT, width=3)
        if label:
            # Label sits above the box, or inside it when the box touches the top edge.
            text = self.create_text(
                x0 + 6, y0 - 4 if y0 > 24 else y0 + 4,
                text=label,
                anchor=tk.SW if y0 > 24 else tk.NW,
                fill=theme.ACCENT_FG,
                font="TkHeadingFont",
            )
            bx0, by0, bx1, by1 = self.bbox(text)
            backdrop = self.create_rectangle(
                bx0 - 4, by0 - 2, bx1 + 4, by1 + 2, fill=theme.ACCENT, outline=""
            )
            self.tag_lower(backdrop, text)
