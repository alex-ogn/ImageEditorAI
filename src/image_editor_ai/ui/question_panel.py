"""Bottom panel where the user asks an object detection question about the image."""

import tkinter as tk
from collections.abc import Callable

from image_editor_ai.ui import theme


class QuestionPanel(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_submit: Callable[[], None],
        on_change: Callable[[], None],
    ) -> None:
        super().__init__(master, bg=theme.PANEL_BG)

        row = tk.Frame(self, bg=theme.PANEL_BG)
        row.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 4))
        tk.Label(
            row, text="Question", bg=theme.PANEL_BG, fg=theme.HEADER_FG, font="TkHeadingFont"
        ).pack(side=tk.LEFT, padx=(0, 10))

        self._question = tk.StringVar(self)
        self._question.trace_add("write", lambda *_args: on_change())
        entry = tk.Entry(
            row,
            textvariable=self._question,
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
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        entry.bind("<Return>", lambda _e: on_submit())
        entry.bind("<KP_Enter>", lambda _e: on_submit())

        self._result = tk.Label(
            self,
            text="Ask what to find, e.g. “Where is the dog?”, then click “Detect Objects”.",
            bg=theme.PANEL_BG,
            fg=theme.HINT_FG,
            font="TkDefaultFont",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        self._result.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0, 10))

    @property
    def question(self) -> str:
        return self._question.get().strip()

    def set_result(self, text: str, highlight: bool = False) -> None:
        self._result.config(text=text, fg=theme.HEADER_FG if highlight else theme.HINT_FG)
