"""Main application window."""

import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image

from image_editor_ai import APP_NAME
from image_editor_ai.ai.image_ai import (
    Detection,
    describe_image,
    edit_image,
    detect_object,
    format_detection,
)
from image_editor_ai.config import load_settings
from image_editor_ai.imaging import SUPPORTED_EXTENSIONS, load_image
from image_editor_ai.platform_utils import IS_MACOS, shortcut_event, shortcut_label
from image_editor_ai.ui.description_panel import DescriptionPanel
from image_editor_ai.ui.header import Header
from image_editor_ai.ui.image_view import ImageView
from image_editor_ai.ui.prompt_panel import PromptPanel

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

        # AI requests run off the Tk thread; at most one of each kind at a time.
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._image_name = ""
        self._edit_job: Future[Image.Image] | None = None
        self._edit_image: Image.Image | None = None
        self._edit_request = ""
        self._describe_job: Future[str] | None = None
        self._describe_image: Image.Image | None = None
        self._detect_job: Future[Detection] | None = None
        self._detect_image: Image.Image | None = None
        # Generated description of the image currently shown (None until generated).
        self._description: str | None = None

        self._build_menu()
        self.header = Header(
            self,
            on_open=self.open_image,
            on_describe=self.generate_description,
            on_edit=self.ai_edit,
            on_detect=self.detect_objects,
        )
        self.header.pack(side=tk.TOP, fill=tk.X)
        self.description_panel = DescriptionPanel(self)
        self.description_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.prompt_panel = PromptPanel(
            self,
            on_detect=self.detect_objects,
            on_edit=self.ai_edit,
            on_change=self._refresh_buttons,
        )
        self.prompt_panel.pack(side=tk.BOTTOM, fill=tk.X)
        self.image_view = ImageView(self)
        self.image_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._refresh_buttons()

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
        self._image_name = path.name
        self._show_image(image, "Generate a description, then ask what to find or edit.")

    def _show_image(self, image: Image.Image, status: str, highlight: bool = False) -> None:
        """Make `image` the current one; its description has to be generated again."""
        self.image_view.set_image(image)
        self.title(f"{self._image_name} — {APP_NAME}")
        self._description = None
        self.description_panel.show_hint('Click "Generate Description" to describe this image.')
        self.prompt_panel.set_status(status, highlight)
        self._refresh_buttons()

    def _refresh_buttons(self) -> None:
        has_image = self.image_view.image is not None
        # Description needs an open image; shown as busy while a request runs.
        self.header.set_describe_state(enabled=has_image, busy=self._describe_job is not None)
        # Detection also needs this image's description and a question to ask.
        can_detect = (
            has_image and self._description is not None and bool(self.prompt_panel.question)
        )
        self.header.set_detect_state(enabled=can_detect, busy=self._detect_job is not None)
        # Editing needs an open image and a modification request.
        self.header.set_edit_state(
            enabled=has_image and bool(self.prompt_panel.edit_request),
            busy=self._edit_job is not None,
        )

    def generate_description(self) -> None:
        image = self.image_view.image
        if image is None or self._describe_job is not None:
            return  # the button is disabled in these states
        self.description_panel.show_hint("Generating description…")
        self._description = None
        self._describe_job = self._executor.submit(describe_image, self.settings, image.copy())
        self._describe_image = image
        self._refresh_buttons()
        self.after(POLL_MS, self._poll_description)

    def _poll_description(self) -> None:
        job = self._describe_job
        if job is None:
            return
        if not job.done():
            self.after(POLL_MS, self._poll_description)
            return
        self._describe_job = None
        if self._describe_image is not self.image_view.image:
            self._refresh_buttons()
            return  # a different image was opened meanwhile; drop the stale result
        try:
            self._description = job.result()
            self.description_panel.set_description(self._description)
        except Exception as exc:  # config, network and API errors
            self.description_panel.show_hint("Description failed.")
            messagebox.showerror(
                APP_NAME, f"Could not generate a description:\n{exc}", parent=self
            )
        self._refresh_buttons()

    def detect_objects(self) -> None:
        image, question = self.image_view.image, self.prompt_panel.question
        if image is None or self._description is None or not question or self._detect_job:
            return  # the button is disabled in these states
        self.prompt_panel.set_status("Detecting…")
        self._detect_job = self._executor.submit(
            detect_object, self.settings, image.copy(), self._description, question
        )
        self._detect_image = image
        self._refresh_buttons()
        self.after(POLL_MS, self._poll_detection)

    def _poll_detection(self) -> None:
        job = self._detect_job
        if job is None:
            return
        if not job.done():
            self.after(POLL_MS, self._poll_detection)
            return
        self._detect_job = None
        self._refresh_buttons()
        if self._detect_image is not self.image_view.image:
            return  # a different image was opened meanwhile; drop the stale result
        try:
            detection = job.result()
        except Exception as exc:  # config, image size, network and API errors
            self.prompt_panel.set_status("Detection failed.")
            messagebox.showerror(APP_NAME, f"Could not detect objects:\n{exc}", parent=self)
            return
        self.image_view.set_detection(detection.box, f"{detection.confidence:.0%}")
        self.prompt_panel.set_status(format_detection(detection), highlight=True)

    def ai_edit(self) -> None:
        image, request = self.image_view.image, self.prompt_panel.edit_request
        if image is None or not request or self._edit_job is not None:
            return  # the button is disabled in these states
        self.prompt_panel.set_status("Editing the image… this can take a while.")
        self._edit_job = self._executor.submit(edit_image, self.settings, image.copy(), request)
        self._edit_image = image
        self._edit_request = request
        self._refresh_buttons()
        self.after(POLL_MS, self._poll_edit)

    def _poll_edit(self) -> None:
        job = self._edit_job
        if job is None:
            return
        if not job.done():
            self.after(POLL_MS, self._poll_edit)
            return
        self._edit_job = None
        self._refresh_buttons()
        if self._edit_image is not self.image_view.image:
            return  # a different image was opened meanwhile; drop the stale result
        try:
            edited = job.result()
        except Exception as exc:  # config, network and API errors
            self.prompt_panel.set_status("Edit failed.")
            messagebox.showerror(APP_NAME, f"Could not edit the image:\n{exc}", parent=self)
            return
        # The edited image replaces the current one, so further edits build on it.
        self.prompt_panel.clear_edit_request()
        self._show_image(edited, f"Edit applied: “{self._edit_request}”", highlight=True)

    def destroy(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().destroy()


def main() -> None:
    MainWindow().mainloop()
