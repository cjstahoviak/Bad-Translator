# Bad Translator

> Play telephone with Google Translate — intentionally mangled English guaranteed.

Bad Translator takes your English text, runs it through a configurable number of
random languages via Google Translate, then translates back to English. The
compounding translation errors produce hilariously broken output — the more hops,
the worse the result.

**▶ Try it: [calvinstahoviak.com/bad-translator](https://calvinstahoviak.com/bad-translator)**

---

## How It Works

1. The text is translated through **N** randomly selected languages (default: 10).
2. The result is translated back to English.

Each hop compounds the errors of the last, producing increasingly nonsensical
output. The language chain is displayed so you can see the path taken.

**Example:**
```
English → Japanese → Swahili → Arabic → Finnish → Dutch → Korean → Welsh → Turkish → Hungarian → English

Input:  "To be or not to be, that is the question."
Output: "Being or not existing, this is the problem."
```

Everything runs in your browser. Translation uses Google's free public translate
endpoint directly via `fetch` — there is no backend and no API key.

---

## Run Locally

It's a static site — just serve the folder with any web server:

```bash
git clone https://github.com/cjstahoviak/Bad-Translator.git
cd Bad-Translator
python3 -m http.server 8000
# then open http://localhost:8000/
```

---

## Project Structure

```
Bad-Translator/
├── .github/workflows/
│   └── pages.yml     # Builds & deploys the site to GitHub Pages on push to main
├── index.html        # The single page
├── styles.css        # Styling (dark theme)
├── app.js            # Translation engine + UI logic
└── Examples/         # Sample text files
```

---

## Deployment

The site is served via **GitHub Pages** from this repository. Because the custom
domain `calvinstahoviak.com` is configured on the `calvinstahoviak.github.io`
user-site repo, this project page is automatically available at
`calvinstahoviak.com/bad-translator`.

Pushing to `main` triggers `.github/workflows/pages.yml`, which uploads the repo
root and deploys it. (One-time setup: in **Settings → Pages**, set the source to
**GitHub Actions**.)

---

## Notes

- The translation endpoint (`translate.googleapis.com/translate_a/single`) is
  unofficial — it needs no key and is CORS-friendly, but Google could rate-limit
  or change it. Fine for a hobby gag; if it ever breaks, the fix would be a small
  serverless proxy to a translation API.
