"""Canvas that displays an image fitted to all available space."""

import tkinter as tk

from PIL import Image, ImageTk

from image_editor_ai.imaging import fit_size
from image_editor_ai.platform_utils import shortcut_label
from image_editor_ai.ui import theme

RESIZE_DEBOUNCE_MS = 50


class ImageView(tk.Canvas):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=theme.CANVAS_BG, highlightthickness=0, borderwidth=0)
        self._original: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None  # keep a reference or Tk drops it
        self._pending_render: str | None = None
        self.bind("<Configure>", self._on_configure)

    @property
    def image(self) -> Image.Image | None:
        return self._original

    def set_image(self, image: Image.Image) -> None:
        self._original = image
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
        self.create_image(box_w // 2, box_h // 2, image=self._photo, anchor=tk.CENTER)
