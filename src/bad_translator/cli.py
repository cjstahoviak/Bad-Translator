"""Command-line interface for Bad Translator.

Usage examples:
    bad-translator "Hello, world!"
    bad-translator -n 5 "Hello, world!"
    bad-translator -f Examples/Gnome.txt
    echo "Some text" | bad-translator
    bad-translator --no-spell "Hello, world!"
"""

from __future__ import annotations

import argparse
import sys

from bad_translator.core import BadTranslator, BadTranslatorError, correct_spelling


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bad-translator",
        description="Play telephone with Google Translate — intentionally mangled English guaranteed.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  bad-translator 'Hello, world!'\n"
            "  bad-translator -n 5 'Hello, world!'\n"
            "  bad-translator -f Examples/Gnome.txt\n"
            "  echo 'Some text' | bad-translator"
        ),
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to translate. Omit to read from stdin.",
    )
    parser.add_argument(
        "-n",
        "--rounds",
        type=int,
        default=10,
        metavar="INT",
        help="Number of intermediate language hops (default: 10).",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r", encoding="utf-8"),
        metavar="PATH",
        help="Read input text from a file instead of the command line.",
    )
    parser.add_argument(
        "--no-spell",
        action="store_true",
        help="Skip spell correction before translation.",
    )
    return parser


def main() -> None:
    """Entry point for the ``bad-translator`` console script."""
    parser = _build_parser()
    args = parser.parse_args()

    # --- Validate rounds ---------------------------------------------------
    if args.rounds < 1:
        parser.error("--rounds must be at least 1.")

    # --- Gather input text -------------------------------------------------
    if args.file:
        raw = args.file.read()
        args.file.close()
    elif args.text:
        raw = " ".join(args.text)
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    raw = raw.strip()
    if not raw:
        print("error: input text is empty.", file=sys.stderr)
        sys.exit(1)

    # --- Optional spell correction ----------------------------------------
    if not args.no_spell:
        raw = correct_spelling(raw)

    # --- Run translation ---------------------------------------------------
    try:
        translator = BadTranslator()
        result = translator.translate(raw, num_rounds=args.rounds)
    except BadTranslatorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- Output -----------------------------------------------------------
    print(result.chain_display)
    print()
    print(result.output)


if __name__ == "__main__":
    main()
