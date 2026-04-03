"""Unit tests for bad_translator.core.

All calls to the external ``translators`` library and ``SpellChecker`` are
mocked so that the test suite runs offline and deterministically.
"""

from __future__ import annotations

import pytest

from bad_translator.core import (
    BadTranslator,
    BadTranslatorError,
    TranslationResult,
    correct_spelling,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_LANGUAGES = {
    "en": "English",
    "ja": "Japanese",
    "sw": "Swahili",
    "fr": "French",
    "de": "German",
}


@pytest.fixture()
def translator(mocker):
    """Return a BadTranslator whose language list is patched to FAKE_LANGUAGES."""
    mocker.patch(
        "bad_translator.core.ts.get_languages",
        return_value=FAKE_LANGUAGES,
    )
    return BadTranslator()


# ---------------------------------------------------------------------------
# TranslationResult
# ---------------------------------------------------------------------------


class TestTranslationResult:
    def test_chain_display_joins_with_arrows(self):
        result = TranslationResult(
            output="mangled",
            language_chain=["English", "Japanese", "English"],
        )
        assert result.chain_display == "English → Japanese → English"

    def test_chain_display_single_entry(self):
        result = TranslationResult(output="hi", language_chain=["English"])
        assert result.chain_display == "English"

    def test_chain_display_empty(self):
        result = TranslationResult(output="hi", language_chain=[])
        assert result.chain_display == ""


# ---------------------------------------------------------------------------
# BadTranslator.translate — happy path
# ---------------------------------------------------------------------------


class TestBadTranslatorTranslate:
    def test_returns_translation_result(self, translator, mocker):
        mocker.patch("bad_translator.core.ts.translate_text", return_value="mangled")
        result = translator.translate("Hello", num_rounds=3)
        assert isinstance(result, TranslationResult)
        assert result.output == "mangled"

    def test_chain_length_equals_rounds_plus_two(self, translator, mocker):
        """Chain should be: English + N foreign langs + English = N + 2 entries."""
        mocker.patch("bad_translator.core.ts.translate_text", return_value="x")
        num_rounds = 5
        result = translator.translate("Hello", num_rounds=num_rounds)
        assert len(result.language_chain) == num_rounds + 2

    def test_chain_starts_and_ends_with_english(self, translator, mocker):
        mocker.patch("bad_translator.core.ts.translate_text", return_value="x")
        result = translator.translate("Hello", num_rounds=4)
        assert result.language_chain[0] == "English"
        assert result.language_chain[-1] == "English"

    def test_api_called_rounds_plus_one_times(self, translator, mocker):
        """translate_text should be called N times (intermediate) + 1 (final → en)."""
        mock = mocker.patch(
            "bad_translator.core.ts.translate_text", return_value="x"
        )
        num_rounds = 4
        translator.translate("Hello", num_rounds=num_rounds)
        assert mock.call_count == num_rounds + 1

    def test_final_destination_is_english(self, translator, mocker):
        """The last API call must target 'en'."""
        calls = []

        def fake_translate(text, translator, from_language, to_language):
            calls.append(to_language)
            return "x"

        mocker.patch("bad_translator.core.ts.translate_text", side_effect=fake_translate)
        translator.translate("Hello", num_rounds=3)
        assert calls[-1] == "en"

    def test_single_round(self, translator, mocker):
        mocker.patch("bad_translator.core.ts.translate_text", return_value="bonjour")
        result = translator.translate("Hello", num_rounds=1)
        assert result.output == "bonjour"
        assert len(result.language_chain) == 3  # English → X → English


# ---------------------------------------------------------------------------
# BadTranslator.translate — error handling
# ---------------------------------------------------------------------------


class TestBadTranslatorErrors:
    def test_api_failure_raises_bad_translator_error(self, translator, mocker):
        mocker.patch(
            "bad_translator.core.ts.translate_text",
            side_effect=Exception("network error"),
        )
        with pytest.raises(BadTranslatorError, match="Translation failed"):
            translator.translate("Hello", num_rounds=1)

    def test_empty_text_raises_value_error(self, translator):
        with pytest.raises(ValueError, match="empty"):
            translator.translate("", num_rounds=5)

    def test_whitespace_only_raises_value_error(self, translator):
        with pytest.raises(ValueError, match="empty"):
            translator.translate("   ", num_rounds=5)

    def test_zero_rounds_raises_value_error(self, translator):
        with pytest.raises(ValueError, match="num_rounds"):
            translator.translate("Hello", num_rounds=0)

    def test_negative_rounds_raises_value_error(self, translator):
        with pytest.raises(ValueError, match="num_rounds"):
            translator.translate("Hello", num_rounds=-1)

    def test_get_languages_failure_raises_bad_translator_error(self, mocker):
        mocker.patch(
            "bad_translator.core.ts.get_languages",
            side_effect=Exception("unreachable"),
        )
        with pytest.raises(BadTranslatorError, match="Could not load language list"):
            BadTranslator()


# ---------------------------------------------------------------------------
# correct_spelling
# ---------------------------------------------------------------------------


class TestCorrectSpelling:
    def test_corrects_simple_misspelling(self, mocker):
        """'teh' should be corrected to 'the'."""
        mocker.patch(
            "bad_translator.core._spell.split_words",
            return_value=["teh", "world"],
        )
        mocker.patch(
            "bad_translator.core._spell.correction",
            side_effect=lambda w: {"teh": "the", "world": "world"}.get(w),
        )
        assert correct_spelling("teh world") == "the world"

    def test_none_correction_falls_back_to_original_word(self, mocker):
        """If SpellChecker.correction() returns None, the original word is kept."""
        mocker.patch(
            "bad_translator.core._spell.split_words",
            return_value=["xyzzy"],
        )
        mocker.patch("bad_translator.core._spell.correction", return_value=None)
        assert correct_spelling("xyzzy") == "xyzzy"

    def test_empty_string_returns_empty(self, mocker):
        mocker.patch("bad_translator.core._spell.split_words", return_value=[])
        assert correct_spelling("") == ""

    def test_multiple_words_joined_with_spaces(self, mocker):
        mocker.patch(
            "bad_translator.core._spell.split_words",
            return_value=["hello", "wrold"],
        )
        mocker.patch(
            "bad_translator.core._spell.correction",
            side_effect=lambda w: {"hello": "hello", "wrold": "world"}.get(w),
        )
        result = correct_spelling("hello wrold")
        assert result == "hello world"
