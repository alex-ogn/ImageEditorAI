# AGENTS.md

Guidance for AI coding agents (and humans) working on **ImageEditorAI** — a desktop app
for creative and interactive AI features over images.

## Key points (must always hold)

1. **Cross-platform: Windows, macOS and Linux.** Every change must work on all three.
   - Use only the standard library and cross-platform dependencies. No OS-specific APIs
     (`winreg`, `os.startfile`, `ctypes.windll`, AppleScript, …) and no shell calls
     (`os.system`, `subprocess` with shell commands).
   - Build paths with `pathlib`; never hardcode `\` or `/` separators or absolute paths.
   - Keyboard shortcuts go through `image_editor_ai.platform_utils` — `Command` on macOS,
     `Control` elsewhere — and menu accelerator labels must match (`⌘O` vs `Ctrl+O`).
   - Mouse wheel: handle both `<MouseWheel>` (Windows/macOS) and `<Button-4>`/`<Button-5>` (Linux).
   - Fonts: use Tk named fonts (`TkDefaultFont`, `TkHeadingFont`, …), never OS-specific font names.
     Set colors explicitly so the UI looks the same everywhere.
   - File dialog `filetypes` use space-separated patterns, plus an "All files" entry.
   - Layout math uses widget sizes (`winfo_width`/`winfo_height`, `<Configure>` events) — no
     hardcoded screen sizes or DPI assumptions.
2. **Tech stack:** Python 3.12 + tkinter + Pillow. AI features use models from
   [OpenRouter](https://openrouter.ai) via `httpx` (`src/image_editor_ai/ai/openrouter.py`).
3. **Secrets:** the OpenRouter API key lives only in `.env` (loaded by `config.py` with
   python-dotenv). Never commit `.env`, never log or display the key. Document new settings
   in `.env.example`.
4. **Dependencies:** declared in `pyproject.toml`; all direct *and transitive* dependencies are
   pinned in `uv.lock` (committed). Add/remove with `uv add <pkg>` / `uv remove <pkg>`
   (`--group dev` for dev tools). **Never use or create `requirements.txt`.**
5. **Virtual environment:** the project runs in `.venv`, created and kept in sync by `uv sync`.
   Run things with `uv run …`.
6. **Image display:** an opened image fills all available working space below the header
   (logo + command bar) and its **aspect ratio is never changed**. Always resize from the
   original image with one uniform scale factor (`imaging.fit_size`).

## Project layout

```
src/image_editor_ai/
  app.py            MainWindow + main() entry point
  config.py         .env loading, Settings
  imaging.py        pure image helpers (fit_size, load_image)
  platform_utils.py OS detection, shortcut helpers
  ui/header.py      logo + command bar
  ui/image_view.py  canvas that shows the fitted image
  ai/openrouter.py  OpenRouter API client
tests/              pytest tests
```

## Commands

```bash
uv sync                    # create/update .venv from uv.lock
uv run image-editor-ai     # start the app
uv run pytest              # run tests
```

Keep pure logic (geometry, image processing, API payloads) out of Tk widgets so it can be
unit-tested without a display.
