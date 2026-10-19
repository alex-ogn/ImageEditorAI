"""Main application window."""

import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image

from image_editor_ai import APP_NAME
from image_editor_ai.ai.image_ai import describe_image
from image_editor_ai.config import load_settings
from image_editor_ai.imaging import SUPPORTED_EXTENSIONS, load_image
from image_editor_ai.platform_utils import IS_MACOS, shortcut_event, shortcut_label
from image_editor_ai.ui.description_panel import DescriptionPanel
from image_editor_ai.ui.header import Header
from image_editor_ai.ui.image_view import ImageView

FILE_TYPES = [
    ("Images", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
    ("All files", "*"),
]
POLL_MS = 100


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.title(APP_NAME)
        self.geometry("1200x800")
        self.minsize(640, 420)

        # AI requests run off the Tk thread; one at a time.
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._describe_job: Future[str] | None = None
        self._describe_image: Image.Image | None = None

        self._build_menu()
        self.header = Header(self, on_open=self.open_image, on_describe=self.generate_description)
        self.header.pack(side=tk.TOP, fill=tk.X)
        self.description_panel = DescriptionPanel(self)
        self.description_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_view = ImageView(self)
        self.image_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.bind_all(shortcut_event("o"), lambda _e: self.open_image())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(
            label="Open…", accelerator=shortcut_label("o"), command=self.open_image
        )
        if not IS_MACOS:  # macOS provides Quit in the application menu
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def open_image(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self, title="Open image", filetypes=FILE_TYPES
        )
        if not filename:
            return
        path = Path(filename)
        try:
            image = load_image(path)
        except Exception as exc:  # Pillow raises several error types
            messagebox.showerror(APP_NAME, f"Could not open {path.name}:\n{exc}", parent=self)
            return
        self.image_view.set_image(image)
        self.title(f"{path.name} — {APP_NAME}")
        self.description_panel.show_hint('Click "Generate Description" to describe this image.')

    def generate_description(self) -> None:
        image = self.image_view.image
        if image is None:
            messagebox.showinfo(APP_NAME, "Open an image first.", parent=self)
            return
        if self._describe_job is not None:
            return
        self.header.set_describe_busy(True)
        self.description_panel.show_hint("Generating description…")
        self._describe_job = self._executor.submit(describe_image, self.settings, image.copy())
        self._describe_image = image
        self.after(POLL_MS, self._poll_description)

    def _poll_description(self) -> None:
        job = self._describe_job
        if job is None:
            return
        if not job.done():
            self.after(POLL_MS, self._poll_description)
            return
        self._describe_job = None
        self.header.set_describe_busy(False)
        if self._describe_image is not self.image_view.image:
            return  # a different image was opened meanwhile; drop the stale result
        try:
            self.description_panel.set_description(job.result())
        except Exception as exc:  # config, network and API errors
            self.description_panel.show_hint("Description failed.")
            messagebox.showerror(
                APP_NAME, f"Could not generate a description:\n{exc}", parent=self
            )

    def destroy(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().destroy()


def main() -> None:
    MainWindow().mainloop()
