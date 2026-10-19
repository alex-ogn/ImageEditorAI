"""Top bar with the app logo and the command bar."""

import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont

from image_editor_ai import APP_NAME
from image_editor_ai.platform_utils import shortcut_label
from image_editor_ai.ui import theme


class Header(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_open: Callable[[], None],
        on_describe: Callable[[], None],
    ) -> None:
        super().__init__(master, bg=theme.HEADER_BG, height=theme.HEADER_HEIGHT)
        self.pack_propagate(False)

        self._build_logo()
        self._build_command_bar(on_open, on_describe)

    def _build_logo(self) -> None:
        base = tkfont.nametofont("TkDefaultFont")
        badge_font = base.copy()
        badge_font.configure(size=12, weight="bold")
        title_font = base.copy()
        title_font.configure(size=14, weight="bold")

        logo = tk.Frame(self, bg=theme.HEADER_BG)
        logo.pack(side=tk.LEFT, padx=(12, 24))

        size = 34
        badge = tk.Canvas(
            logo, width=size, height=size, bg=theme.HEADER_BG, highlightthickness=0
        )
        badge.create_oval(1, 1, size - 1, size - 1, fill=theme.ACCENT, outline="")
        badge.create_text(size / 2, size / 2, text="AI", fill=theme.ACCENT_FG, font=badge_font)
        badge.pack(side=tk.LEFT)

        tk.Label(
            logo, text=APP_NAME, bg=theme.HEADER_BG, fg=theme.HEADER_FG, font=title_font
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _build_command_bar(
        self, on_open: Callable[[], None], on_describe: Callable[[], None]
    ) -> None:
        bar = tk.Frame(self, bg=theme.HEADER_BG)
        bar.pack(side=tk.LEFT, fill=tk.Y, pady=10)

        self._button(bar, f"Open…  ({shortcut_label('o')})", on_open)
        self.describe_button = self._button(bar, "Generate Description", on_describe)
        # Placeholder for an upcoming AI feature.
        self._button(bar, "AI Edit", None)

    def set_describe_state(self, enabled: bool, busy: bool = False) -> None:
        active = enabled and not busy
        self.describe_button.config(
            text="Generating…" if busy else "Generate Description",
            state=tk.NORMAL if active else tk.DISABLED,
            cursor="hand2" if active else "",
        )

    @staticmethod
    def _button(parent: tk.Misc, text: str, command: Callable[[], None] | None) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            state=tk.NORMAL if command else tk.DISABLED,
            bg=theme.BUTTON_BG,
            fg=theme.HEADER_FG,
            activebackground=theme.BUTTON_ACTIVE_BG,
            activeforeground=theme.HEADER_FG,
            disabledforeground=theme.BUTTON_DISABLED_FG,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            cursor="hand2" if command else "",
        )
        btn.pack(side=tk.LEFT, padx=4, fill=tk.Y)
        return btn
