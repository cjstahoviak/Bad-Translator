# Lost in Translation — CLAUDE.md

## Project Overview

Lost in Translation is a hobby/entertainment web app that plays "telephone" with Google
Translate. It takes English text, runs it through a configurable number of random
intermediate languages, then translates back to English — producing intentionally
broken, humorous output.

It is a **static, single-page web app** (no backend, no build step). All logic runs
in the browser. It is deployed via GitHub Pages and served at
`calvinstahoviak.com/lost-in-translation`.

---

## Repository Structure

```
lost-in-translation/
├── .github/
│   └── workflows/
│       └── pages.yml       # Deploys the static site to GitHub Pages on push to main
├── index.html              # The single page (markup + layout)
├── styles.css              # Styling (dark theme, responsive)
├── app.js                  # Translation engine + UI wiring
├── Examples/               # Sample text files (Gnome.txt, test_book.txt)
├── README.md
└── CLAUDE.md
```

---

## Tech Stack

- **HTML / CSS / vanilla JavaScript** — no framework, no bundler, no build step.
- **Translation:** Google's free public endpoint
  `https://translate.googleapis.com/translate_a/single` called directly via
  `fetch` — no API key, CORS-friendly.
- **Hosting:** GitHub Pages (project page under the account's custom domain).

---

## Running

```bash
# Serve the static files with any local web server, e.g.:
python3 -m http.server 8000
# then open http://localhost:8000/
```

There are no dependencies to install and nothing to compile.

---

## Core Logic (`app.js`)

### `badTranslate(text, rounds, onHop)`

1. Start with English (`en`) input.
2. Loop `rounds` times:
   - Pick a random code from `FOREIGN_CODES` (all of `LANGUAGES` except `en`).
   - Translate from the current language to the chosen one via `translateOnce`.
   - Append the language name to the chain and invoke the optional `onHop` callback.
3. Translate the final result back to English.
4. Return `{ output, chain }`.

### `translateOnce(text, src, dest)`

`fetch`es the Google endpoint with `client=gtx&sl=<src>&tl=<dest>&dt=t&q=<text>`,
parses the nested JSON response (`data[0]` is an array of `[segment, ...]`),
concatenates the segments, and throws a descriptive `Error` on network/HTTP/parse
failure or empty result.

### `LANGUAGES` / `FOREIGN_CODES`

`LANGUAGES` is a hardcoded `code → display name` map of Google-supported languages
(replaces the old Python `translators.get_languages("google")` call, which has no
browser equivalent). `FOREIGN_CODES` is its keys minus `en`.

---

## UI (`index.html` + `app.js`)

- Header: title + tagline.
- Two side-by-side textareas: editable **Input (English)** and read-only **Output**.
- Controls: **Rounds** number input (default 10) + **TRANSLATE** button.
- Status area: language-chain line, an indeterminate loading bar (shown during
  translation), and an inline error message.
- `Ctrl/Cmd+Enter` in the input triggers a translation.

Translation is async (`await`); the UI disables the button and shows the loader
while hops are in flight, and the chain updates live via the `onHop` callback.

---

## Deployment

GitHub Pages serves the repo root. Pushing to `main` runs
`.github/workflows/pages.yml`, which uploads the root and deploys with
`actions/deploy-pages`. One-time manual setup: **Settings → Pages → Source:
GitHub Actions**.

The custom domain (`calvinstahoviak.com`) lives on the `calvinstahoviak.github.io`
user-site repo and applies account-wide, so this project page is automatically
reachable at `calvinstahoviak.com/lost-in-translation`. Do **not** add a `CNAME` file
here — it would conflict with the user-site domain config.

---

## Known Limitations

- The `translate_a/single` endpoint is unofficial — it can rate-limit or change if
  Google alters it. It's the only practical no-backend, no-key option; the fallback
  would be a small serverless proxy to a translation API.
- No spell correction (the old Python `pyspellchecker` step was dropped — no clean
  static-browser equivalent). Could be re-added later with a JS library like
  `nspell` if desired.
- No offline mode; an internet connection is required for translation.
