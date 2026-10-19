"""Bottom panel with the object detection question, the AI edit request and a status line."""

import tkinter as tk
from collections.abc import Callable

from image_editor_ai.ui import theme


class PromptPanel(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_detect: Callable[[], None],
        on_edit: Callable[[], None],
        on_change: Callable[[], None],
    ) -> None:
        super().__init__(master, bg=theme.PANEL_BG)

        fields = tk.Frame(self, bg=theme.PANEL_BG)
        fields.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 4))
        fields.columnconfigure(1, weight=1)
        self._question = self._field(fields, 0, "Question", on_detect, on_change)
        self._edit_request = self._field(fields, 1, "Edit request", on_edit, on_change)

        self._status = tk.Label(
            self,
            text="Open an image to get started.",
            bg=theme.PANEL_BG,
            fg=theme.HINT_FG,
            font="TkDefaultFont",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        self._status.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0, 10))

    @staticmethod
    def _field(
        parent: tk.Frame,
        row: int,
        label: str,
        on_submit: Callable[[], None],
        on_change: Callable[[], None],
    ) -> tk.StringVar:
        tk.Label(
            parent, text=label, bg=theme.PANEL_BG, fg=theme.HEADER_FG, font="TkHeadingFont"
        ).grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=3)

        value = tk.StringVar(parent)
        value.trace_add("write", lambda *_args: on_change())
        entry = tk.Entry(
            parent,
            textvariable=value,
            bg=theme.BUTTON_BG,
            fg=theme.HEADER_FG,
            insertbackground=theme.HEADER_FG,
            selectbackground=theme.ACCENT,
            selectforeground=theme.ACCENT_FG,
            disabledbackground=theme.BUTTON_BG,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=theme.BUTTON_BG,
            highlightcolor=theme.ACCENT,
            font="TkTextFont",
        )
        entry.grid(row=row, column=1, sticky=tk.EW, pady=3, ipady=5)
        entry.bind("<Return>", lambda _e: on_submit())
        entry.bind("<KP_Enter>", lambda _e: on_submit())
        return value

    @property
    def question(self) -> str:
        return self._question.get().strip()

    @property
    def edit_request(self) -> str:
        return self._edit_request.get().strip()

    def clear_edit_request(self) -> None:
        self._edit_request.set("")

    def set_status(self, text: str, highlight: bool = False) -> None:
        self._status.config(text=text, fg=theme.HEADER_FG if highlight else theme.HINT_FG)
