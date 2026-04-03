"""Core translation engine for Bad Translator.

This module is shared by both the GUI and CLI interfaces. It contains:
- BadTranslator: the main class that runs the telephone-game algorithm.
- TranslationResult: a dataclass holding the output and language chain.
- BadTranslatorError: raised when the translation service fails.
- correct_spelling: a utility that spell-corrects text before translation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import translators as ts
from spellchecker import SpellChecker

# Initialise the spell checker once at module load (loading the dictionary is slow).
_spell = SpellChecker(language="en")


class BadTranslatorError(Exception):
    """Raised when the translation API call fails."""


@dataclass
class TranslationResult:
    """The output of a Bad Translator run.

    Attributes:
        output: The final (mangled) English text.
        language_chain: Ordered list of language names visited, e.g.
            ["English", "Japanese", "Swahili", ..., "English"].
    """

    output: str
    language_chain: list[str] = field(default_factory=list)

    @property
    def chain_display(self) -> str:
        """Human-readable arrow-separated chain, e.g. "English → Japanese → English"."""
        return " → ".join(self.language_chain)


class BadTranslator:
    """Runs the telephone-game translation algorithm.

    The algorithm:
    1. Optionally spell-correct the input.
    2. Loop *num_rounds* times, each time translating the current text into
       a randomly chosen language.
    3. Translate the final result back to English.

    Uses the ``translators`` library which wraps several free translation
    services (defaulting to Google Translate) without requiring an API key.
    """

    # The translator engine to use.  "google" works without credentials.
    _ENGINE = "google"

    def __init__(self) -> None:
        # Fetch the language list once; it returns a dict of {code: name}.
        try:
            self._languages: dict[str, str] = ts.get_languages(self._ENGINE)
        except Exception as exc:
            raise BadTranslatorError(
                f"Could not load language list from {self._ENGINE}: {exc}"
            ) from exc

        # Remove English from the pool so every intermediate hop is a foreign language.
        self._foreign_languages = {
            code: name for code, name in self._languages.items() if code != "en"
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate(self, text: str, num_rounds: int = 10) -> TranslationResult:
        """Translate *text* through *num_rounds* random languages and back to English.

        Args:
            text: The English input text (should be spell-corrected first).
            num_rounds: Number of intermediate language hops (must be >= 1).

        Returns:
            A TranslationResult with the mangled output and the language chain.

        Raises:
            BadTranslatorError: If any API call fails.
            ValueError: If *num_rounds* < 1 or *text* is empty.
        """
        if not text or not text.strip():
            raise ValueError("Input text must not be empty.")
        if num_rounds < 1:
            raise ValueError("num_rounds must be at least 1.")

        current_text = text
        current_lang = "en"
        chain: list[str] = [self._languages.get("en", "English")]

        for _ in range(num_rounds):
            target_lang = random.choice(list(self._foreign_languages))
            current_text = self._call_api(current_text, current_lang, target_lang)
            chain.append(self._foreign_languages[target_lang])
            current_lang = target_lang

        # Final hop back to English.
        current_text = self._call_api(current_text, current_lang, "en")
        chain.append(self._languages.get("en", "English"))

        return TranslationResult(output=current_text, language_chain=chain)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_api(self, text: str, src: str, dest: str) -> str:
        """Wrap a single translators API call with error handling."""
        try:
            result = ts.translate_text(
                text,
                translator=self._ENGINE,
                from_language=src,
                to_language=dest,
            )
            return result if isinstance(result, str) else str(result)
        except Exception as exc:
            raise BadTranslatorError(
                f"Translation failed ({src} → {dest}): {exc}"
            ) from exc


def correct_spelling(text: str) -> str:
    """Return *text* with misspelled words corrected using pyspellchecker.

    Unknown words for which no correction can be found are left unchanged.
    This guards against the ``SpellChecker.correction()`` returning ``None``
    in newer versions of pyspellchecker.

    Args:
        text: Raw input text.

    Returns:
        Spell-corrected text (word-level only, punctuation preserved).
    """
    words = _spell.split_words(text)
    corrected = [_spell.correction(word) or word for word in words]
    return " ".join(corrected)
