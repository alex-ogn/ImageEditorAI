# ImageEditorAI

Cross-platform (Windows, macOS, Linux) desktop app for creative and interactive AI features
over images. Built with Python, tkinter and Pillow; AI features use models from
[OpenRouter](https://openrouter.ai).

## Setup

1. Install [uv](https://docs.astral.sh/uv/):
   - Windows: `winget install --id astral-sh.uv`
   - macOS: `brew install uv`
   - Linux / macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Create the virtual environment (`.venv`) and install the locked dependencies:
   ```bash
   uv sync
   ```
   uv downloads Python 3.12 automatically if needed (it includes tkinter).
3. Configure OpenRouter:
   ```bash
   cp .env.example .env
   ```
   Then put your key in `OPENROUTER_API_KEY` inside `.env`. The vision model
   (`OPENROUTER_MODEL`) and the prompt used by **Generate Description** (`DESCRIBE_PROMPT`)
   are preset there and can be changed if needed. **Detect Objects** uses TypeSafe's Jev
   model (`DETECT_MODEL`) through OpenRouter's Decisions API, with the same key.

## Features

- **Generate Description** — describes the open image in the right-hand panel.
- **Detect Objects** — type a question in the bottom panel (for example "Where is the dog?").
  Jev gets the image, its description and your question, and draws a box around the best
  match, showing its confidence. It needs an open image and a generated description.

## Run

```bash
uv run image-editor-ai
```

## Test

```bash
uv run pytest
```

## Dependencies

All dependencies, including transitive ones, are managed by `pyproject.toml` and pinned in
`uv.lock`. Use `uv add <package>` / `uv remove <package>` — there is no `requirements.txt`.

See [AGENTS.md](AGENTS.md) for the project rules.
