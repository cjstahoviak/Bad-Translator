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
- **Type:** Fredoka (display/UI) + Nunito (body) from Google Fonts, `display=swap`
  with a system-font fallback stack. The only external asset besides the
  translate endpoint.
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

`onHop(chain, done, total)` fires after every completed hop. `total` is
`rounds + 1` — the trip home to English counts as a hop — which is what drives
the determinate progress bar.

### `translateOnce(text, src, dest)`

`fetch`es the Google endpoint with `client=gtx&sl=<src>&tl=<dest>&dt=t&q=<text>`,
parses the nested JSON response (`data[0]` is an array of `[segment, ...]`),
concatenates the segments, and throws a descriptive `Error` on network/HTTP/parse
failure or empty result.

### `LANGUAGES` / `FOREIGN_CODES`

`LANGUAGES` is a hardcoded `code → display name` map of Google-supported languages
(replaces the old Python `translators.get_languages("google")` call, which has no
browser equivalent). `FOREIGN_CODES` is its keys minus `en`.

### `EXAMPLES`

Short excerpts behind the 🎲 button, each `{ text, title, author }`. Everything in
the list is **strictly US public domain** (pre-1929 publication) — Frost, Poe,
Dickens, Melville, Austen, Carroll, Blake, Dickinson, Sandburg, Shakespeare. Keep
it that way when adding entries, and keep them short (~100–300 chars) so a run
stays quick.

---

## UI (`index.html` + `app.js`)

The page is a vertical pipeline — input on top, the language relay in the middle,
output below — so the relay animation gets full width to work with:

1. **Top bar** — theme toggle, pinned right.
2. **Header** — big centered title, "Translation" in coral; tagline
   "play telephone with randomized languages!".
3. **Input panel** — editable textarea + a 🎲 button that loads a public-domain
   passage and credits it underneath.
4. **Relay stage** — see below.
5. **Output panel** — read-only textarea + a copy button.
6. **Controls** — **Rounds** number input (default 10) + **TRANSLATE** button.
7. **Status** — determinate progress bar ("hop 4 of 11") + inline error message.
8. **Footer** — name + source link.

`Ctrl/Cmd+Enter` in the input triggers a translation. Translation is async; the
UI disables the button and shows the progress bar while hops are in flight.

### Visual system (`styles.css`)

"Chunky sticker": 3px ink outlines (`--bw`), hard offset shadows with no blur
(`--shadow`), rounded display type, warm cream background with a faint dot grid.
Buttons physically press down on `:active`. All colors are custom properties
defined in full on bare `:root` (light); `:root[data-theme="dark"]` redefines
only the color tokens.

Theme is **light by default** — deliberately, not from `prefers-color-scheme`.
The choice persists in `localStorage["lit-theme"]` and a small blocking script in
`<head>` stamps `data-theme` before first paint so a dark reload doesn't flash.

Placeholders are muted + italic with `opacity: 1` (Firefox dims them otherwise);
the read-only output textarea renders at full-strength `--ink` so real output is
never mistaken for placeholder text.

### Relay stage

`.relay-track` is a `1fr auto 1fr` grid: the equal side columns pin the arrow to
dead center no matter how many languages have piled up. Past languages live in
the right-aligned left column, the current one in the left-aligned right column.

Chips are **absolutely positioned and moved with `transform` only** — layout
never changes, so `offsetWidth` stays stable and every move animates cleanly.
`layoutPast()` walks outward from the arrow, stacking each chip at its depth's
scale (`DEPTH_SCALE` / `DEPTH_OPACITY`, capped at 4 — 2 on narrow screens).

On each hop `Relay.push()`:
1. `demoteCurrent()` moves the current chip into the past row, re-anchoring it at
   its existing on-screen position so the handoff has no jump.
2. Overflow chips are dropped from the left end — harmless, since positions are
   computed from the arrow outwards.
3. `playTransit()` dips the crossing chip's opacity to ~0 and back via the Web
   Animations API. Hiding it behind the arrow instead would only work for names
   narrower than the arrow, which "Chinese (Simplified)" is not.

Chip widths depend on Fredoka, so `document.fonts.ready` triggers a re-layout.
The screen-reader chain lives in a visually-hidden `aria-live` element; the relay
itself is `aria-hidden`.

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
- The relay measures chip widths in pixels, so it assumes the fonts have settled.
  `document.fonts.ready` covers the normal case; a font that loads much later
  would leave the spacing slightly off until the next hop re-runs `layoutPast()`.
