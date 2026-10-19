"""Right-hand panel that shows the AI-generated image description."""

import tkinter as tk

from image_editor_ai.ui import theme

PANEL_WIDTH = 360


class DescriptionPanel(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=theme.PANEL_BG, width=PANEL_WIDTH)
        self.pack_propagate(False)

        tk.Label(
            self,
            text="Description",
            bg=theme.PANEL_BG,
            fg=theme.HEADER_FG,
            font="TkHeadingFont",
            anchor=tk.W,
        ).pack(side=tk.TOP, fill=tk.X, padx=12, pady=(12, 6))

        body = tk.Frame(self, bg=theme.PANEL_BG)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(12, 4), pady=(0, 12))

        scrollbar = tk.Scrollbar(body, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._text = tk.Text(
            body,
            wrap=tk.WORD,
            bg=theme.PANEL_BG,
            fg=theme.HEADER_FG,
            insertbackground=theme.HEADER_FG,
            selectbackground=theme.ACCENT,
            selectforeground=theme.ACCENT_FG,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            font="TkTextFont",
            padx=4,
            pady=4,
            yscrollcommand=scrollbar.set,
        )
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._text.yview)
        self._text.tag_configure("hint", foreground=theme.HINT_FG)

        self.show_hint('Open an image and click "Generate Description".')

    def show_hint(self, message: str) -> None:
        self._set(message, "hint")

    def set_description(self, text: str) -> None:
        self._set(text)

    def _set(self, text: str, *tags: str) -> None:
        # Read-only for the user, but text stays selectable and copyable.
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", text, tags)
        self._text.config(state=tk.DISABLED)
        self._text.yview_moveto(0)
