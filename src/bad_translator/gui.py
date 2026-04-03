"""CustomTkinter GUI for Bad Translator.

Layout (grid-based, resizable):
┌──────────────────────────────────────────────────────┐
│  Bad Translator                            [☀ / 🌙]  │  ← title + theme toggle
├─────────────────────┬────────────────────────────────┤
│  Input              │  Output                        │  ← two ScrolledText boxes
│  (editable)         │  (read-only)                   │
├─────────────────────┴────────────────────────────────┤
│  Rounds: [10]   [Browse]   [TRANSLATE]               │  ← controls
├──────────────────────────────────────────────────────┤
│  English → Zulu → Arabic → ... → English             │  ← language chain label
│  [████████████░░░░░░░░]  Translating...              │  ← progress bar (hidden when idle)
└──────────────────────────────────────────────────────┘

Translation is run in a background thread so the UI never freezes.
"""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from bad_translator.core import BadTranslator, BadTranslatorError, correct_spelling

# Default appearance — can be toggled at runtime.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Resolve the Examples/ directory relative to this file's location so the
# file browser works regardless of where the app is launched from.
_EXAMPLES_DIR = Path(__file__).parent.parent.parent / "Examples"


class App(ctk.CTk):
    """Main application window."""

    _MIN_WIDTH = 800
    _MIN_HEIGHT = 550
    _DEFAULT_ROUNDS = 10

    def __init__(self) -> None:
        super().__init__()

        self.title("Bad Translator")
        self.minsize(self._MIN_WIDTH, self._MIN_HEIGHT)

        # Start at half-screen size (user can resize freely).
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw // 2}x{sh // 2}")

        self._translator = BadTranslator()
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Make the window expand sensibly.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # text boxes row expands

        # --- Title bar row ------------------------------------------------
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=16, pady=(16, 4), sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_frame,
            text="Bad Translator",
            font=ctk.CTkFont(size=36, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._theme_btn = ctk.CTkButton(
            title_frame,
            text="☀ Light",
            width=90,
            command=self._toggle_theme,
        )
        self._theme_btn.grid(row=0, column=1, sticky="e")

        # --- Text boxes row -----------------------------------------------
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=1, column=0, padx=16, pady=4, sticky="nsew")
        text_frame.grid_columnconfigure((0, 1), weight=1)
        text_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(text_frame, text="Input", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=4
        )
        ctk.CTkLabel(text_frame, text="Output", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=1, sticky="w", padx=4
        )

        self._input_box = ctk.CTkTextbox(text_frame, wrap="word")
        self._input_box.grid(row=1, column=0, padx=(0, 4), sticky="nsew")
        self._input_box.insert("1.0", "Type a sentence here…")

        self._output_box = ctk.CTkTextbox(text_frame, wrap="word", state="disabled")
        self._output_box.grid(row=1, column=1, padx=(4, 0), sticky="nsew")

        # --- Controls row -------------------------------------------------
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=2, column=0, padx=16, pady=4, sticky="ew")

        ctk.CTkLabel(controls_frame, text="Rounds:").pack(side="left", padx=(0, 4))

        self._rounds_var = ctk.StringVar(value=str(self._DEFAULT_ROUNDS))
        self._rounds_entry = ctk.CTkEntry(
            controls_frame, textvariable=self._rounds_var, width=60
        )
        self._rounds_entry.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            controls_frame, text="Browse Files", width=110, command=self._browse_file
        ).pack(side="left", padx=(0, 8))

        self._translate_btn = ctk.CTkButton(
            controls_frame,
            text="TRANSLATE",
            width=130,
            command=self._on_translate,
        )
        self._translate_btn.pack(side="left")

        # --- Chain label + progress bar -----------------------------------
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=3, column=0, padx=16, pady=(4, 4), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self._chain_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(size=11),
            wraplength=700,
            justify="left",
        )
        self._chain_label.grid(row=0, column=0, sticky="w")

        self._progress = ctk.CTkProgressBar(status_frame, mode="indeterminate")
        # Progress bar is hidden until a translation starts.

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_translate(self) -> None:
        """Validate input, then spawn a background translation thread."""
        # Validate rounds.
        try:
            rounds = int(self._rounds_var.get())
            if rounds < 1:
                raise ValueError
        except ValueError:
            self._show_error("Rounds must be a positive integer.")
            return

        raw = self._input_box.get("1.0", "end").strip()
        if not raw:
            self._show_error("Please enter some text to translate.")
            return

        # Disable controls while translating.
        self._set_controls_enabled(False)
        self._chain_label.configure(text="Translating…")
        self._progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self._progress.start()

        # Run translation off the main thread.
        thread = threading.Thread(
            target=self._translate_worker,
            args=(raw, rounds),
            daemon=True,
        )
        thread.start()

    def _translate_worker(self, raw: str, rounds: int) -> None:
        """Background thread: spell-correct, translate, then update the UI."""
        try:
            corrected = correct_spelling(raw)
            result = self._translator.translate(corrected, num_rounds=rounds)
        except BadTranslatorError as exc:
            self.after(0, self._on_translate_error, str(exc))
            return

        self.after(0, self._on_translate_done, result.output, result.chain_display)

    def _on_translate_done(self, output: str, chain: str) -> None:
        """Called on the main thread when translation succeeds."""
        self._output_box.configure(state="normal")
        self._output_box.delete("1.0", "end")
        self._output_box.insert("1.0", output)
        self._output_box.configure(state="disabled")

        self._chain_label.configure(text=chain)
        self._stop_progress()
        self._set_controls_enabled(True)

    def _on_translate_error(self, message: str) -> None:
        """Called on the main thread when translation fails."""
        self._chain_label.configure(text="")
        self._stop_progress()
        self._set_controls_enabled(True)
        self._show_error(f"Translation failed:\n{message}")

    def _browse_file(self) -> None:
        """Open a file dialog to load a .txt file into the input box."""
        initial = str(_EXAMPLES_DIR) if _EXAMPLES_DIR.exists() else "."
        path = filedialog.askopenfilename(
            title="Open text file",
            initialdir=initial,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            text = Path(path).read_text(encoding="utf-8")
            self._input_box.delete("1.0", "end")
            self._input_box.insert("1.0", text)

    def _toggle_theme(self) -> None:
        """Switch between dark and light appearance modes."""
        current = ctk.get_appearance_mode()
        if current.lower() == "dark":
            ctk.set_appearance_mode("light")
            self._theme_btn.configure(text="🌙 Dark")
        else:
            ctk.set_appearance_mode("dark")
            self._theme_btn.configure(text="☀ Light")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._translate_btn.configure(state=state)
        self._rounds_entry.configure(state=state)

    def _stop_progress(self) -> None:
        self._progress.stop()
        self._progress.grid_forget()

    def _show_error(self, message: str) -> None:
        """Display a modal error dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=message, wraplength=340, justify="left").pack(
            padx=24, pady=(20, 8)
        )
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy).pack(pady=(0, 16))


def main() -> None:
    """Entry point for the ``bad-translator-gui`` console script."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
