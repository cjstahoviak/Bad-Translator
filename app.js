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
async function badTranslate(text, rounds, onHop) {
  let currentText = text;
  let currentLang = "en";
  const chain = ["English"];

  for (let i = 0; i < rounds; i++) {
    const target = randomForeignCode(currentLang);
    currentText = await translateOnce(currentText, currentLang, target);
    chain.push(LANGUAGES[target]);
    currentLang = target;
    if (onHop) onHop(chain);
  }

  // Final hop back to English.
  currentText = await translateOnce(currentText, currentLang, "en");
  chain.push("English");
  if (onHop) onHop(chain);

  return { output: currentText, chain };
}

// --- UI wiring -------------------------------------------------------------

const inputEl = document.getElementById("input");
const outputEl = document.getElementById("output");
const roundsEl = document.getElementById("rounds");
const buttonEl = document.getElementById("translate");
const chainEl = document.getElementById("chain");
const loaderEl = document.getElementById("loader");
const errorEl = document.getElementById("error");

function setLoading(isLoading) {
  buttonEl.disabled = isLoading;
  loaderEl.hidden = !isLoading;
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = !message;
}

function renderChain(chain) {
  chainEl.textContent = chain.join(" → ");
}

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

  setLoading(true);
  outputEl.value = "";
  chainEl.textContent = "";

  try {
    const { output, chain } = await badTranslate(text, rounds, renderChain);
    outputEl.value = output;
    renderChain(chain);
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
