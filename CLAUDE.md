# Bad Translator — CLAUDE.md

## Project Overview

Bad Translator is a hobby/entertainment Python application that plays "telephone" with Google Translate. It takes English text, runs it through a configurable number of random intermediate languages, then translates back to English — producing intentionally broken, humorous output.

Two interfaces are provided:
- **GUI** (`src/bad_translator/gui.py`) — CustomTkinter desktop app, launched via `bad-translator-gui`
- **CLI** (`src/bad_translator/cli.py`) — argparse console interface, launched via `bad-translator`

Both share a common engine in `src/bad_translator/core.py`.

---

## Repository Structure

```
Bad-Translator/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Lint (ruff) + pytest on every push/PR
│       └── release.yml         # Build PyInstaller executables + GitHub Release on tag push
├── src/
│   └── bad_translator/
│       ├── __init__.py         # Version export (__version__ = "2.0.0")
│       ├── core.py             # BadTranslator class, TranslationResult, correct_spelling
│       ├── cli.py              # argparse CLI entry point
│       └── gui.py              # CustomTkinter GUI entry point
├── tests/
│   ├── __init__.py
│   ├── test_core.py            # Unit tests for core engine (API mocked)
│   └── test_cli.py             # Unit tests for CLI argument handling
├── Examples/
│   ├── Gnome.txt               # Sample text for demo/testing
│   └── test_book.txt           # Simple one-line test text
├── .gitignore
├── pyproject.toml              # Project metadata, dependencies, tool config
├── bad_translator.spec         # PyInstaller build spec
├── README.md
└── CLAUDE.md
```

---

## Tech Stack

- **Language:** Python 3.10+
- **GUI:** `customtkinter>=5.2.2` — modern Tkinter wrapper with dark/light themes
- **Translation:** `translators>=5.9.0` — free multi-engine wrapper (Google, Bing, etc.), no API key required
- **Spell checking:** `pyspellchecker>=0.7.2`
- **Build system:** `hatchling` via `pyproject.toml`
- **Testing:** `pytest`, `pytest-cov`, `pytest-mock`
- **Linting:** `ruff`
- **Distribution:** PyInstaller + GitHub Actions

---

## Setup

```bash
# Clone and install (editable, with dev tools)
git clone https://github.com/cjstahoviak/Bad-Translator.git
cd Bad-Translator
pip install -e ".[dev]"
```

---

## Running

```bash
# GUI (primary)
bad-translator-gui
# or
python -m bad_translator.gui

# CLI
bad-translator "Hello, world!"
bad-translator -n 5 "Hello, world!"
bad-translator -f Examples/Gnome.txt
echo "Some text" | bad-translator
# or
python -m bad_translator.cli "Hello, world!"
```

---

## Testing

```bash
# Run all tests with coverage
pytest

# Run linter
ruff check src/ tests/
```

Tests mock all external API calls — the suite is fully offline and deterministic.

---

## Core Logic

### `BadTranslator.translate(text, num_rounds)`

1. Start with English (`en`) input.
2. Loop `num_rounds` times:
   - Pick a random language from `translators.get_languages("google")` (excluding English).
   - Translate from the current language to the chosen one via `translators.translate_text()`.
3. Translate the final result back to English.
4. Return a `TranslationResult(output, language_chain)`.

### `correct_spelling(text)`

Spell-corrects input using `pyspellchecker`. Guards against `SpellChecker.correction()` returning `None` (a known issue in newer versions) by falling back to the original word.

---

## Key Classes & Functions

| Symbol | File | Description |
|--------|------|-------------|
| `BadTranslator` | `core.py` | Main engine class |
| `TranslationResult` | `core.py` | Dataclass: `output`, `language_chain`, `chain_display` |
| `BadTranslatorError` | `core.py` | Raised on API failure |
| `correct_spelling` | `core.py` | Module-level spell correction utility |
| `App` | `gui.py` | `ctk.CTk` subclass — the main window |
| `main()` | `gui.py` / `cli.py` | Entry point for each interface |

---

## GUI Layout

Window is resizable (min 800×550). Uses `grid` geometry manager throughout.

- Row 0: Title label + theme toggle button (dark/light)
- Row 1: Side-by-side input (editable) and output (read-only) `CTkTextbox` widgets
- Row 2: Controls — Rounds entry, Browse Files button, TRANSLATE button
- Row 3: Language chain label + indeterminate progress bar (shown only during translation)

Translation runs in a `threading.Thread` to keep the UI responsive.

---

## CLI Usage

```
usage: bad-translator [-h] [-n INT] [-f PATH] [--no-spell] [text ...]

positional arguments:
  text          Text to translate (omit for stdin)

options:
  -n, --rounds INT    Number of intermediate language hops (default: 10)
  -f, --file PATH     Read input from a text file
  --no-spell          Skip spell correction
```

---

## Releases

Tag a commit to trigger an automated release:

```bash
git tag v2.0.1
git push origin v2.0.1
```

The `release.yml` workflow builds standalone executables for Linux, Windows, and macOS using PyInstaller, then creates a GitHub Release with those files attached.

---

## Known Limitations

- `translators` is an unofficial library — it can break if Google changes their internal endpoints, though it is actively maintained and supports fallback engines.
- No offline/local translation mode; an internet connection is required.
- GUI tests are not included (CustomTkinter requires a display); core logic and CLI are fully tested.
