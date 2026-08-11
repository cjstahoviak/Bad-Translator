// Lost in Translation — browser port of the original Python BadTranslator engine.
// Runs entirely client-side: it sends text hop-by-hop through random languages
// using Google's free, key-less translate endpoint, then back to English.

"use strict";

// Curated map of Google Translate language code -> display name.
// Replaces the Python `translators.get_languages("google")` call, which has no
// browser equivalent. English ("en") is the fixed start/end and is excluded from
// the random pool below.
const LANGUAGES = {
  af: "Afrikaans", sq: "Albanian", am: "Amharic", ar: "Arabic", hy: "Armenian",
  az: "Azerbaijani", eu: "Basque", be: "Belarusian", bn: "Bengali", bs: "Bosnian",
  bg: "Bulgarian", ca: "Catalan", ceb: "Cebuano", ny: "Chichewa",
  "zh-CN": "Chinese (Simplified)", "zh-TW": "Chinese (Traditional)", co: "Corsican",
  hr: "Croatian", cs: "Czech", da: "Danish", nl: "Dutch", en: "English",
  eo: "Esperanto", et: "Estonian", tl: "Filipino", fi: "Finnish", fr: "French",
  fy: "Frisian", gl: "Galician", ka: "Georgian", de: "German", el: "Greek",
  gu: "Gujarati", ht: "Haitian Creole", ha: "Hausa", haw: "Hawaiian", he: "Hebrew",
  hi: "Hindi", hmn: "Hmong", hu: "Hungarian", is: "Icelandic", ig: "Igbo",
  id: "Indonesian", ga: "Irish", it: "Italian", ja: "Japanese", jv: "Javanese",
  kn: "Kannada", kk: "Kazakh", km: "Khmer", ko: "Korean", ku: "Kurdish (Kurmanji)",
  ky: "Kyrgyz", lo: "Lao", la: "Latin", lv: "Latvian", lt: "Lithuanian",
  lb: "Luxembourgish", mk: "Macedonian", mg: "Malagasy", ms: "Malay", ml: "Malayalam",
  mt: "Maltese", mi: "Maori", mr: "Marathi", mn: "Mongolian", my: "Myanmar (Burmese)",
  ne: "Nepali", no: "Norwegian", ps: "Pashto", fa: "Persian", pl: "Polish",
  pt: "Portuguese", pa: "Punjabi", ro: "Romanian", ru: "Russian", sm: "Samoan",
  gd: "Scots Gaelic", sr: "Serbian", st: "Sesotho", sn: "Shona", sd: "Sindhi",
  si: "Sinhala", sk: "Slovak", sl: "Slovenian", so: "Somali", es: "Spanish",
  su: "Sundanese", sw: "Swahili", sv: "Swedish", tg: "Tajik", ta: "Tamil",
  te: "Telugu", th: "Thai", tr: "Turkish", uk: "Ukrainian", ur: "Urdu",
  uz: "Uzbek", vi: "Vietnamese", cy: "Welsh", xh: "Xhosa", yi: "Yiddish",
  yo: "Yoruba", zu: "Zulu",
};

// Pool of foreign language codes (everything except English).
const FOREIGN_CODES = Object.keys(LANGUAGES).filter((code) => code !== "en");

const ENDPOINT = "https://translate.googleapis.com/translate_a/single";

// Upper bound on rounds (mirrors the `max` on the HTML input). High values fire
// many sequential requests and invite rate-limiting from the free endpoint.
const MAX_ROUNDS = 50;

// The free GET endpoint sends the text in the query string, which truncates or
// rejects long input. Guard against it with a friendly error.
const MAX_INPUT_CHARS = 1500;

// Translate a single hop. Mirrors BadTranslator._call_api in the Python version.
async function translateOnce(text, src, dest) {
  const url =
    `${ENDPOINT}?client=gtx&sl=${encodeURIComponent(src)}` +
    `&tl=${encodeURIComponent(dest)}&dt=t&q=${encodeURIComponent(text)}`;

  let response;
  try {
    response = await fetch(url);
  } catch (err) {
    throw new Error(`Translation failed (${src} → ${dest}): network error`);
  }
  if (!response.ok) {
    throw new Error(`Translation failed (${src} → ${dest}): HTTP ${response.status}`);
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    throw new Error(`Translation failed (${src} → ${dest}): bad response`);
  }

  // Response shape: [[[ "segment", ... ], ...], ...]. Concatenate every segment.
  const segments = Array.isArray(data) && Array.isArray(data[0]) ? data[0] : [];
  const result = segments
    .map((seg) => (Array.isArray(seg) ? seg[0] : ""))
    .join("");

  if (!result) {
    throw new Error(`Translation failed (${src} → ${dest}): empty result`);
  }
  return result;
}

// Pick a random foreign code, avoiding `exclude` so consecutive hops never land
// on the same language (which would be a wasted, no-op round-trip).
function randomForeignCode(exclude) {
  let code;
  do {
    code = FOREIGN_CODES[Math.floor(Math.random() * FOREIGN_CODES.length)];
  } while (code === exclude && FOREIGN_CODES.length > 1);
  return code;
}

// Run text through `rounds` random languages, then back to English.
// Mirrors BadTranslator.translate. Returns { output, chain }.
//
// `onHop(chain, done, total)` fires after every completed hop — `total` is
// `rounds + 1` because the trip home to English counts as a hop.
async function badTranslate(text, rounds, onHop) {
  let currentText = text;
  let currentLang = "en";
  const chain = ["English"];
  const total = rounds + 1;

  for (let i = 0; i < rounds; i++) {
    const target = randomForeignCode(currentLang);
    currentText = await translateOnce(currentText, currentLang, target);
    chain.push(LANGUAGES[target]);
    currentLang = target;
    if (onHop) onHop(chain, i + 1, total);
  }

  // Final hop back to English.
  currentText = await translateOnce(currentText, currentLang, "en");
  chain.push("English");
  if (onHop) onHop(chain, total, total);

  return { output: currentText, chain };
}

// --- Sample text -----------------------------------------------------------

// Short excerpts from works in the public domain, kept well under
// MAX_INPUT_CHARS so a run stays quick.
const EXAMPLES = [
  {
    title: "The Road Not Taken",
    author: "Robert Frost",
    text: "Two roads diverged in a yellow wood,\nAnd sorry I could not travel both\nAnd be one traveler, long I stood\nAnd looked down one as far as I could\nTo where it bent in the undergrowth;",
  },
  {
    title: "Jabberwocky",
    author: "Lewis Carroll",
    text: "'Twas brillig, and the slithy toves\nDid gyre and gimble in the wabe;\nAll mimsy were the borogoves,\nAnd the mome raths outgrabe.",
  },
  {
    title: "The Raven",
    author: "Edgar Allan Poe",
    text: "Once upon a midnight dreary, while I pondered, weak and weary,\nOver many a quaint and curious volume of forgotten lore—",
  },
  {
    title: "Ozymandias",
    author: "Percy Bysshe Shelley",
    text: "I met a traveller from an antique land\nWho said: Two vast and trunkless legs of stone\nStand in the desert.",
  },
  {
    title: "A Tale of Two Cities",
    author: "Charles Dickens",
    text: "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness.",
  },
  {
    title: "Moby-Dick",
    author: "Herman Melville",
    text: "Call me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse, I thought I would sail about a little and see the watery part of the world.",
  },
  {
    title: "Pride and Prejudice",
    author: "Jane Austen",
    text: "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
  },
  {
    title: "Fog",
    author: "Carl Sandburg",
    text: "The fog comes on little cat feet.\nIt sits looking over harbor and city on silent haunches and then moves on.",
  },
  {
    title: "Hope is the thing with feathers",
    author: "Emily Dickinson",
    text: "Hope is the thing with feathers that perches in the soul, and sings the tune without the words, and never stops at all.",
  },
  {
    title: "The Tyger",
    author: "William Blake",
    text: "Tyger Tyger, burning bright,\nIn the forests of the night;\nWhat immortal hand or eye\nCould frame thy fearful symmetry?",
  },
  {
    title: "The Tell-Tale Heart",
    author: "Edgar Allan Poe",
    text: "True!—nervous—very, very dreadfully nervous I had been and am; but why will you say that I am mad?",
  },
  {
    title: "Alice's Adventures in Wonderland",
    author: "Lewis Carroll",
    text: "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do.",
  },
  {
    title: "Sonnet 18",
    author: "William Shakespeare",
    text: "Shall I compare thee to a summer's day?\nThou art more lovely and more temperate.",
  },
];

// --- UI wiring -------------------------------------------------------------

const inputEl = document.getElementById("input");
const outputEl = document.getElementById("output");
const roundsEl = document.getElementById("rounds");
const buttonEl = document.getElementById("translate");
const chainEl = document.getElementById("chain");
const errorEl = document.getElementById("error");
const progressEl = document.getElementById("progress");
const progressFillEl = document.getElementById("progress-fill");
const progressLabelEl = document.getElementById("progress-label");
const relayEl = document.getElementById("relay");
const pastEl = document.getElementById("relay-past");
const nextEl = document.getElementById("relay-next");
const arrowEl = document.getElementById("relay-arrow");
const themeBtn = document.getElementById("theme-toggle");
const themeGlyphEl = document.getElementById("theme-glyph");
const shuffleBtn = document.getElementById("shuffle");
const creditEl = document.getElementById("example-credit");
const copyBtn = document.getElementById("copy");
const copyLabelEl = document.getElementById("copy-label");

// --- Theme -----------------------------------------------------------------

const THEME_KEY = "lit-theme";

function applyTheme(theme) {
  const dark = theme === "dark";
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  themeBtn.setAttribute("aria-pressed", String(dark));
  themeGlyphEl.textContent = dark ? "☀" : "☾";
  try {
    localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
  } catch (err) { /* storage disabled — the toggle still works for this visit */ }
}

themeBtn.addEventListener("click", () => {
  applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
});

// --- Relay -----------------------------------------------------------------

// Each step further from the arrow shrinks and fades. Length caps how many
// past languages stay on screen.
const DEPTH_SCALE = [0.92, 0.75, 0.6, 0.47];
const DEPTH_OPACITY = [0.85, 0.58, 0.36, 0.2];
const CHIP_GAP = 12;
const ARROW_GAP = 10;

const narrowQuery = window.matchMedia("(max-width: 560px)");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

// Long language names crowd a phone screen, so keep a shorter tail there.
function maxPast() {
  return narrowQuery.matches ? 2 : DEPTH_SCALE.length;
}

function makeChip(name, className) {
  const chip = document.createElement("span");
  chip.className = `chip ${className}`;
  chip.textContent = name;
  return chip;
}

// Walk the past chips from the arrow outwards, stacking each one to the left of
// the previous at its depth's scale. Positions are pure transforms, so nothing
// reflows and every change animates.
function layoutPast() {
  const chips = Array.from(pastEl.children); // oldest → newest
  let cursor = ARROW_GAP;

  for (let i = chips.length - 1; i >= 0; i--) {
    const chip = chips[i];
    const depth = chips.length - 1 - i;
    const scale = DEPTH_SCALE[depth] ?? 0;
    chip.style.transform = `translate(${-cursor}px, -50%) scale(${scale})`;
    chip.style.opacity = String(DEPTH_OPACITY[depth] ?? 0);
    cursor += chip.offsetWidth * scale + CHIP_GAP;
  }
}

// Hand the current language off to the past row without a visual jump: it keeps
// its on-screen position, then glides (behind the arrow) into its new slot.
function demoteCurrent(chip) {
  const before = chip.getBoundingClientRect();
  chip.classList.remove("chip-current");
  chip.classList.add("chip-past");
  chip.style.animation = "none";
  pastEl.appendChild(chip);

  const anchor = pastEl.getBoundingClientRect();
  chip.style.transition = "none";
  chip.style.transform = `translate(${before.right - anchor.right}px, -50%) scale(1)`;
  chip.style.opacity = "1";
  return chip;
}

// The chip has to cross the arrow to reach the past row. Dip it to near-nothing
// on the way so it reads as passing *through* — hiding it behind the arrow
// instead would only work for names narrower than the arrow itself.
function playTransit(chip) {
  if (reduceMotion.matches || !chip.animate) return;
  chip.transit = chip.animate(
    [{ opacity: 1 }, { opacity: 0.05, offset: 0.45 }, { opacity: 1 }],
    { duration: 450, easing: "ease-in-out" }
  );
}

const Relay = {
  reset() {
    pastEl.replaceChildren();
    nextEl.replaceChildren(makeChip("English", "chip-current"));
  },

  push(name) {
    // A hop can land before the previous crossing finishes; drop any in-flight
    // fade so it can't fight the new depth's opacity.
    for (const chip of pastEl.children) {
      if (chip.transit) chip.transit.cancel();
    }

    const demoted = nextEl.firstElementChild
      ? demoteCurrent(nextEl.firstElementChild)
      : null;

    // Trimming from the left end never shifts the survivors: the row is
    // positioned from the arrow outwards.
    while (pastEl.children.length > maxPast()) {
      pastEl.firstElementChild.remove();
    }

    nextEl.replaceChildren(makeChip(name, "chip-current"));

    arrowEl.classList.remove("zap");
    void arrowEl.offsetWidth; // restart the animation
    arrowEl.classList.add("zap");

    if (demoted) {
      void pastEl.offsetWidth; // commit the jump-free start position first
      demoted.style.transition = "";
    }
    layoutPast();
    if (demoted) playTransit(demoted);
  },
};

// Chip size is breakpoint-dependent, so any resize invalidates the measured
// positions — not just crossing the narrow-screen threshold.
let relayResize;
window.addEventListener("resize", () => {
  clearTimeout(relayResize);
  relayResize = setTimeout(() => {
    while (pastEl.children.length > maxPast()) {
      pastEl.firstElementChild.remove();
    }
    layoutPast();
  }, 120);
});

// Chip widths depend on Fredoka, so re-measure once it lands.
if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(layoutPast);
}

// --- Status ----------------------------------------------------------------

function setProgress(done, total) {
  progressFillEl.style.width = `${Math.round((done / total) * 100)}%`;
  progressLabelEl.textContent = `hop ${done} of ${total}`;
}

function setLoading(isLoading) {
  buttonEl.disabled = isLoading;
  shuffleBtn.disabled = isLoading;
  progressEl.hidden = !isLoading;
  relayEl.classList.toggle("is-running", isLoading);
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = !message;
}

function setOutput(text) {
  outputEl.value = text;
  copyBtn.disabled = !text;
}

// --- Actions ---------------------------------------------------------------

let lastExample = -1;

shuffleBtn.addEventListener("click", () => {
  let index = lastExample;
  while (index === lastExample && EXAMPLES.length > 1) {
    index = Math.floor(Math.random() * EXAMPLES.length);
  }
  lastExample = index;

  const example = EXAMPLES[index];
  inputEl.value = example.text;
  creditEl.textContent = `— ${example.title}, ${example.author}`;
  creditEl.hidden = false;
  showError("");
});

inputEl.addEventListener("input", () => {
  creditEl.hidden = true;
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(outputEl.value);
    copyLabelEl.textContent = "copied!";
  } catch (err) {
    copyLabelEl.textContent = "copy failed";
  }
  setTimeout(() => {
    copyLabelEl.textContent = "copy";
  }, 1200);
});

async function onTranslate() {
  const text = inputEl.value.trim();
  const rounds = parseInt(roundsEl.value, 10);

  showError("");
  if (!text) {
    showError("Please enter some text to translate.");
    return;
  }
  if (text.length > MAX_INPUT_CHARS) {
    showError(`Input is too long (max ${MAX_INPUT_CHARS} characters). Try a shorter passage.`);
    return;
  }
  if (!Number.isInteger(rounds) || rounds < 1) {
    showError("Rounds must be a whole number of at least 1.");
    return;
  }
  if (rounds > MAX_ROUNDS) {
    showError(`Rounds must be ${MAX_ROUNDS} or fewer.`);
    return;
  }

  // Zero the bar while it's still hidden, so it doesn't rewind from the last run.
  setProgress(0, rounds + 1);
  setLoading(true);
  setOutput("");
  chainEl.textContent = "";
  Relay.reset();

  const onHop = (chain, done, total) => {
    Relay.push(chain[chain.length - 1]);
    chainEl.textContent = chain.join(" → ");
    setProgress(done, total);
  };

  try {
    const { output } = await badTranslate(text, rounds, onHop);
    setOutput(output);
  } catch (err) {
    showError(err.message || "Something went wrong during translation.");
  } finally {
    setLoading(false);
  }
}

buttonEl.addEventListener("click", onTranslate);

// Ctrl/Cmd+Enter from the input triggers a translation.
inputEl.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    onTranslate();
  }
});

// --- Init ------------------------------------------------------------------

applyTheme(document.documentElement.dataset.theme === "dark" ? "dark" : "light");
Relay.reset();
