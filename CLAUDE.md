# Bad Translator - CLAUDE.md

## Project Overview

Bad Translator is a hobby/entertainment Python application that plays "telephone" with Google Translate. It takes English text, runs it through a configurable number of random intermediate languages, then translates back to English — producing intentionally broken, humorous output.

Two interfaces are provided:
- **GUI** (`src/badtranslateGUI.py`) — Tkinter desktop app, the primary entry point
- **CLI** (`src/badtranslate.py`) — Console-based interactive version

## Repository Structure

```
Bad-Translator/
├── README.md
├── CLAUDE.md
├── home.jpg                  # Screenshot used in README
├── src/
│   ├── badtranslateGUI.py    # Main GUI application (entry point)
│   ├── badtranslate.py       # CLI version
│   └── testing.py            # Minimal diagnostic script for googletrans
└── Examples/
    ├── Gnome.txt             # Sample text for demo/testing
    └── test_book.txt         # Simple one-line test text
```

## Tech Stack

- **Language:** Python 3.6+
- **GUI:** Tkinter (stdlib) with `tkinter.ttk`, `scrolledtext`, `messagebox`, `filedialog`
- **Translation:** `googletrans==3.1.0a0` (unofficial async Google Translate wrapper)
- **Spell checking:** `pyspellchecker`

## Setup

```bash
# System dependencies
sudo apt-get install python3.6 python3-pip python3-tk

# Python dependencies
pip3 install pyspellchecker
pip install googletrans==3.1.0a0
```

> The `googletrans` version is pinned to `3.1.0a0` — other versions break the API.

## Running

```bash
# GUI application (primary)
python3 src/badtranslateGUI.py

# CLI application
python3 src/badtranslate.py

# Diagnostic: verify googletrans is working
python3 src/testing.py
```

## Core Logic

Both interfaces share the same translation algorithm:

1. Start with English (`en`) input
2. Loop N times (user-configurable, default 10):
   - Pick a random language from `googletrans.LANGUAGES`
   - Translate from the current language to the random one
3. Translate the final result back to English
4. Return the mangled output

Input is spell-corrected via `pyspellchecker` before translation to prevent API errors from typos.

**Key functions in `badtranslateGUI.py`:**
- `ruinSentenceGUI(string, numRounds, parse_title)` — core algorithm for GUI, updates language chain label
- `ruinSentence(string, numRounds)` — core algorithm for CLI, prints language chain to stdout
- `correctSpelling(string)` — spell-corrects input using `SpellChecker`
- `translateCallback(...)` — button click handler; orchestrates spell-check → translate → display
- `open_file(user_txtbx)` — file browser opening `../Examples` for `.txt` files
- `mainGUI()` — builds and launches the Tkinter window

## GUI Layout

Window is sized to half the screen dimensions and is non-resizable.

- Top half: large "Bad Translator" title label
- Middle: language count entry + language chain display label
- Bottom-left: scrollable input text box
- Bottom-right: scrollable output text box (read-only after translation)
- Buttons: TRANSLATE, INSTRUCTIONS, Browse Files

## CLI Usage

```
-> <text>        Translate text through the configured number of languages
-> -n <number>   Change the number of languages
-> q             Quit
```

## Known Issues / Gotchas

- **No error handling** around the `googletrans` API calls — if the service is unavailable or rate-limits, the app will crash.
- `googletrans` is an unofficial library that relies on scraping Google Translate's internal API. It can break without warning if Google changes their endpoints.
- The file browser's `initialdir` is hardcoded to `"../Examples"` (relative to `src/`), so it only works correctly when launched from the `src/` directory or the project root.
- `spell.correction(word)` can return `None` in newer versions of `pyspellchecker`, which would cause a crash — no guard exists for this.
- There are no automated tests; `testing.py` is a one-off diagnostic script, not a test suite.

## Development Notes

- No `requirements.txt`, `setup.py`, or virtual environment configuration exists. Dependencies must be installed manually per the README.
- The project has no linting, formatting, or CI configuration.
- Both `badtranslateGUI.py` and `badtranslate.py` duplicate the `ruinSentence` logic — they are not shared via a common module.
