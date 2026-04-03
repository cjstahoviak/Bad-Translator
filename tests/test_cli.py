"""Unit tests for bad_translator.cli.

The BadTranslator engine and correct_spelling are mocked so tests run
offline without any real API calls.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from bad_translator.cli import main
from bad_translator.core import BadTranslatorError, TranslationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_RESULT = TranslationResult(
    output="Cheese is a type of hat.",
    language_chain=["English", "Japanese", "Swahili", "English"],
)


def _run(args: list[str], *, stdin_text: str | None = None):
    """Run main() with the given sys.argv args and return (stdout, stderr, exit_code)."""
    import io
    import sys

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    exit_code = 0
    with (
        patch("sys.argv", ["bad-translator"] + args),
        patch("sys.stdout", stdout_capture),
        patch("sys.stderr", stderr_capture),
    ):
        if stdin_text is not None:
            with patch("sys.stdin", io.StringIO(stdin_text)):
                patch("sys.stdin.isatty", return_value=False).start()
                try:
                    main()
                except SystemExit as e:
                    exit_code = e.code or 0
        else:
            try:
                main()
            except SystemExit as e:
                exit_code = e.code or 0

    return stdout_capture.getvalue(), stderr_capture.getvalue(), exit_code


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCliBasic:
    def test_translates_positional_text(self, mocker):
        mocker.patch("bad_translator.cli.correct_spelling", return_value="Hello world")
        mocker.patch(
            "bad_translator.cli.BadTranslator.translate", return_value=FAKE_RESULT
        )
        stdout, _, code = _run(["Hello world"])
        assert code == 0
        assert "Cheese is a type of hat." in stdout
        assert "English → Japanese → Swahili → English" in stdout

    def test_default_rounds_is_ten(self, mocker):
        mocker.patch("bad_translator.cli.correct_spelling", return_value="hi")
        mock_translate = mocker.patch(
            "bad_translator.cli.BadTranslator.translate", return_value=FAKE_RESULT
        )
        _run(["hi"])
        _, kwargs = mock_translate.call_args
        assert kwargs.get("num_rounds", mock_translate.call_args[0][1] if mock_translate.call_args[0] else None) == 10

    def test_rounds_flag(self, mocker):
        mocker.patch("bad_translator.cli.correct_spelling", return_value="hi")
        mock_translate = mocker.patch(
            "bad_translator.cli.BadTranslator.translate", return_value=FAKE_RESULT
        )
        _run(["-n", "5", "hi"])
        # Check that num_rounds=5 was passed
        call_args = mock_translate.call_args
        num_rounds = call_args[1].get("num_rounds") or call_args[0][1]
        assert num_rounds == 5

    def test_no_spell_flag_skips_correction(self, mocker):
        mock_spell = mocker.patch("bad_translator.cli.correct_spelling")
        mocker.patch(
            "bad_translator.cli.BadTranslator.translate", return_value=FAKE_RESULT
        )
        _run(["--no-spell", "Hello"])
        mock_spell.assert_not_called()

    def test_spell_correction_applied_by_default(self, mocker):
        mock_spell = mocker.patch(
            "bad_translator.cli.correct_spelling", return_value="Hello"
        )
        mocker.patch(
            "bad_translator.cli.BadTranslator.translate", return_value=FAKE_RESULT
        )
        _run(["Hello"])
        mock_spell.assert_called_once()


class TestCliFileInput:
    def test_file_flag_reads_content(self, mocker, tmp_path):
        test_file = tmp_path / "input.txt"
        test_file.write_text("Hello from file", encoding="utf-8")

        mocker.patch("bad_translator.cli.correct_spelling", return_value="Hello from file")
        mock_translate = mocker.patch(
            "bad_translator.cli.BadTranslator.translate", return_value=FAKE_RESULT
        )
        _run(["-f", str(test_file)])
        call_text = mock_translate.call_args[0][0]
        assert "Hello from file" in call_text


class TestCliErrors:
    def test_api_error_exits_with_code_1(self, mocker):
        mocker.patch("bad_translator.cli.correct_spelling", return_value="hi")
        mocker.patch(
            "bad_translator.cli.BadTranslator.translate",
            side_effect=BadTranslatorError("network timeout"),
        )
        _, stderr, code = _run(["hi"])
        assert code == 1
        assert "network timeout" in stderr

    def test_invalid_rounds_exits_nonzero(self, mocker):
        _, _, code = _run(["-n", "abc", "hello"])
        assert code != 0

    def test_zero_rounds_exits_nonzero(self, mocker):
        _, _, code = _run(["-n", "0", "hello"])
        assert code != 0

    def test_empty_text_exits_nonzero(self, mocker):
        mocker.patch("bad_translator.cli.correct_spelling", return_value="")
        _, _, code = _run(["   "])
        assert code != 0

    def test_no_args_exits_nonzero(self):
        """Running with no arguments and no stdin should show help and exit."""
        with patch("sys.stdin.isatty", return_value=True):
            _, _, code = _run([])
        assert code != 0
