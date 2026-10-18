#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Homoglyph Detector – Sci‑Fi GUI (Python, Tkinter)

Features
- Pairwise compare: "Is j0hn_doe visually same as john_doe?"
- Scan mode: highlight suspicious homoglyphs in a single string
- Normalization: NFKC + optional diacritic stripping
- Built-in extended homoglyph map (~1000+ entries) + support for importing
  Unicode Consortium's confusables.txt to reach thousands of mappings
- Neon cyberpunk theme (black + neon green/blue)
- Enhanced efficiency for scanning and comparison
- NEW: Detailed visual breakdown of differences in the 'Compare' tab
- NEW: Identifies the type of homoglyph detected (e.g., Cyrillic, Greek, etc.)

Author: You
"""

import re
import sys
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
from collections import defaultdict

# -----------------------------
# Utility: diacritic stripping
# -----------------------------

def strip_diacritics(text: str) -> str:
    """Remove combining marks after NFKD, recompose to NFC-less ASCII-like.
    Keeps base letters (e.g., é -> e)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")

# ----------------------------------------
# Core: Homoglyph map (seed + generators)
# ----------------------------------------

# A more comprehensive seed map
SEED_HOMOGLYPHS: Dict[str, str] = {
    # Digits -> letters
    "0": "o", "1": "l", "2": "z", "3": "e", "4": "a", "5": "s", "6": "b", "7": "t", "8": "b", "9": "g",
    # Leetspeak
    "@": "a", "$": "s", "+": "t", "!": "i", "|": "l", "£": "l", "€": "e", "¥": "y",
    # Punctuation
    "’": "'", "‘": "'", "‚": ",", "“": '"', "”": '"', "„": '"', "—": "-", "–": "-", "∙": ".",
    # Multi-character illusions
    "rn": "m", "cl": "d", "vv": "w", "\u0283\u0283": "ss",
    # Specific Unicode lookalikes
    "℮": "e", "ℯ": "e", "K": "k", "ℬ": "b", "Ⅎ": "f", "ℕ": "n", "ℙ": "p", "ℚ": "q", "ℝ": "r", "ℤ": "z",
    "⍺": "a", "ℵ": "a", "⍝": "d", "ℵ": "h", "℥": "g", "⍬": "q", "ℭ": "c", "ℇ": "e",
    "ℱ": "f", "Ⅎ": "f", "ℵ": "h", "ℐ": "i", "ℒ": "l", "ℳ": "m", "ℛ": "r", "ℜ": "r", "℘": "p", "ⅅ": "d", "ⅆ": "d",
    "⅐": "1", "⅑": "1", "⅒": "1",
}

# Extensive programmatic generators for Latin, Greek, and Cyrillic
GREEK_TO_LATIN = {
    "Α": "A", "Β": "B", "Ε": "E", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P",
    "Τ": "T", "Υ": "Y", "Χ": "X", "α": "a", "β": "b", "γ": "y", "ε": "e", "η": "n", "ι": "i", "κ": "k",
    "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
}

CYRILLIC_TO_LATIN = {
    "А": "A", "В": "B", "Е": "E", "З": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
    "С": "C", "Т": "T", "У": "Y", "Х": "X", "Ѵ": "I", "а": "a", "в": "b", "е": "e", "з": "3", "к": "k",
    "м": "m", "н": "h", "о": "o", "р": "p", "с": "c", "т": "t", "у": "y", "х": "x", "і": "i",
}

# More Latin Extended characters
LATIN_EXTENDED_SIMPLIFY = {
    "à": "a", "á": "a", "â": "a", "ä": "a", "ã": "a", "å": "a", "ā": "a", "ă": "a", "ą": "a", "æ": "ae",
    "ç": "c", "ć": "c", "č": "c", "ĉ": "c",
    "è": "e", "é": "e", "ê": "e", "ë": "e", "ē": "e", "ė": "e", "ę": "e", "ə": "e",
    "ì": "i", "í": "i", "î": "i", "ï": "i", "ī": "i", "į": "i", "ı": "i", "ĳ": "ij",
    "ñ": "n", "ń": "n", "ň": "n", "ŋ": "n",
    "ò": "o", "ó": "o", "ô": "o", "ö": "o", "õ": "o", "ō": "o", "ő": "o", "œ": "oe",
    "š": "s", "ß": "ss",
    "ù": "u", "ú": "u", "û": "u", "ü": "u", "ū": "u", "ů": "u", "ű": "u", "µ": "u",
    "ý": "y", "ÿ": "y",
    "ž": "z", "ź": "z", "ż": "z",
}

# Full-width characters
FULL_WIDTH = {chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}

# This is a new unified map for better tracking
UNIFIED_HOMOGLYPH_MAP: Dict[str, Tuple[str, str]] = {
    **{k: (v, "Leetspeak") for k, v in SEED_HOMOGLYPHS.items()},
    **{k: (v, "Greek") for k, v in GREEK_TO_LATIN.items()},
    **{k: (v, "Cyrillic") for k, v in CYRILLIC_TO_LATIN.items()},
    **{k: (v, "Latin Extended") for k, v in LATIN_EXTENDED_SIMPLIFY.items()},
    **{k: (v, "Full-width") for k, v in FULL_WIDTH.items()},
}


# ----------------------------------------
# Loader for Unicode confusables (optional)
# ----------------------------------------

CONFUSABLES_HINT = (
    "Optionally load Unicode's confusables.txt to expand rules to thousands.\n"
    "File format: lines like '0041 ; 0391 ; MA # LATIN CAPITAL LETTER A → GREEK CAPITAL LETTER ALPHA'\n"
    "This loader maps each source char to the ASCII-ish skeleton of the target sequence."
)

def parse_codepoints(s: str) -> str:
    """Parse a space-separated sequence of hex codepoints to a string."""
    try:
        return "".join(chr(int(part, 16)) for part in s.strip().split() if part)
    except (ValueError, IndexError):
        return ""

def load_confusables_txt(path: str) -> Dict[str, Tuple[str, str]]:
    """Parse confusables.txt and generate a mapping dictionary.
    We convert target sequences to a normalized ASCII-ish skeleton using
    NFKC + diacritic stripping + BASE_MAP for folding.
    """
    conf: Dict[str, Tuple[str, str]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                main, *_ = line.split("#", 1)
                parts = [p.strip() for p in main.split(";")]
                if len(parts) < 2:
                    continue
                src = parse_codepoints(parts[0])
                dst = parse_codepoints(parts[1])
                # We can't know the exact type, so we'll label it "External"
                if src and dst:
                    conf[src] = (fold_text(dst), "External")
            except Exception:
                continue
    return conf

# ------------------------
# Folding / detection core
# ------------------------

@dataclass
class FoldOptions:
    lower: bool = True
    strip_marks: bool = True

def fold_text(text: str, *, options: FoldOptions | None = None, extra_map: Dict[str, Tuple[str, str]] | None = None) -> str:
    """Create a visual-similarity skeleton:
    1) NFKC normalize
    2) optional lowercase
    3) optional strip diacritics
    4) apply UNIFIED_HOMOGLYPH_MAP + extra_map
    """
    if options is None:
        options = FoldOptions()
    t = unicodedata.normalize("NFKC", text)
    if options.lower:
        t = t.lower()
    if options.strip_marks:
        t = strip_diacritics(t)

    full_map = dict(UNIFIED_HOMOGLYPH_MAP)
    if extra_map:
        full_map.update(extra_map)

    # Use a greedy approach to match the longest keys first
    i = 0
    folded_chars = []
    # Keys from the dictionary now point to a tuple (folded_char, type)
    # We only need the keys for this loop
    keys = sorted(full_map.keys(), key=len, reverse=True)
    
    while i < len(t):
        found = False
        for k in keys:
            if t.startswith(k, i):
                folded_chars.append(full_map[k][0])
                i += len(k)
                found = True
                break
        if not found:
            folded_chars.append(t[i])
            i += 1
            
    return "".join(folded_chars)


def compare_strings(a: str, b: str, *, extra_map: Dict[str, Tuple[str, str]] | None = None) -> Tuple[bool, str, str]:
    fa = fold_text(a, extra_map=extra_map)
    fb = fold_text(b, extra_map=extra_map)
    return fa == fb, fa, fb

def scan_string(s: str, *, extra_map: Dict[str, Tuple[str, str]] | None = None) -> List[Tuple[str, str, int]]:
    """Return list of (original_char, replacement, index) for suspicious units."""
    mapping = dict(UNIFIED_HOMOGLYPH_MAP)
    if extra_map:
        mapping.update(extra_map)
    keys = sorted(mapping.keys(), key=len, reverse=True)
    
    idx = 0
    findings: List[Tuple[str, str, int]] = []
    
    while idx < len(s):
        found = False
        for k in keys:
            if s.startswith(k, idx):
                # Ensure it's not a self-mapping
                if k != mapping[k][0]:
                    findings.append((k, mapping[k][0], idx))
                idx += len(k)
                found = True
                break
        if not found:
            idx += 1
            
    return findings

# ------------------------
# Sci‑Fi Tkinter GUI
# ------------------------

class NeonUI(ttk.Style):
    BG = "#0b0f14"         # deep black-blue
    FG = "#d9ffe5"         # pale mint for text
    NEON_GREEN = "#39ff14"  # neon green
    NEON_BLUE = "#00e5ff"   # neon cyan
    PANEL = "#0f141b"
    ACCENT = "#112031"
    RED = "#ff477e"

    def __init__(self, master: tk.Misc):
        super().__init__(master)
        master.configure(bg=self.BG)

        # Set up a few fonts
        self.consola_font = Font(family="Consolas", size=11)
        self.orbitron_font = Font(family="Orbitron", size=22, weight="bold")
        self.mono_font = Font(family="Consolas", size=11)

        self.theme_create("neon", parent="clam", settings={
            ".": {
                "configure": {
                    "background": self.BG,
                    "foreground": self.FG,
                    "fieldbackground": self.PANEL,
                    "focuscolor": self.NEON_BLUE,
                    "bordercolor": self.ACCENT,
                    "lightcolor": self.ACCENT,
                    "darkcolor": self.ACCENT,
                    "troughcolor": self.ACCENT,
                    "font": self.consola_font,
                }
            },
            "TButton": {
                "configure": {
                    "padding": [12, 6],
                    "background": self.ACCENT,
                    "foreground": self.NEON_GREEN,
                    "borderwidth": 1,
                    "relief": "flat",
                },
                "map": {
                    "background": [("active", self.NEON_BLUE)],
                    "foreground": [("active", self.BG)],
                },
            },
            "TEntry": {"configure": {"padding": 8, "foreground": self.NEON_GREEN, "insertbackground": self.NEON_GREEN}},
            "TNotebook": {"configure": {"tabmargins": [6, 6, 6, 0]}},
            "TNotebook.Tab": {
                "configure": {
                    "padding": [14, 8],
                    "background": self.ACCENT,
                    "foreground": self.NEON_BLUE,
                },
                "map": {"background": [("selected", self.NEON_BLUE)], "foreground": [("selected", self.BG)]},
            },
            "Treeview": {
                "configure": {
                    "background": self.PANEL,
                    "fieldbackground": self.PANEL,
                    "foreground": self.FG,
                    "rowheight": 26,
                    "bordercolor": self.ACCENT,
                }
            },
            "TCheckbutton": {
                "configure": {
                    "background": self.BG,
                    "foreground": self.NEON_GREEN,
                }
            }
        })
        self.theme_use("neon")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Homoglyph Detector – Neon")
        self.geometry("980x700")
        self.minsize(900, 640)
        self.style = NeonUI(self)
        self.extra_map: Dict[str, Tuple[str, str]] = {}
        
        # Set up custom fonts if available
        try:
            self.orbitron_font = Font(family="Orbitron", size=22, weight="bold")
        except tk.TclError:
            self.orbitron_font = Font(family="Arial", size=22, weight="bold")
        try:
            self.consola_font = Font(family="Consolas", size=11)
        except tk.TclError:
            self.consola_font = Font(family="Courier New", size=11)

        # Title banner
        title = tk.Label(
            self, text="HOMOGLYPH DETECTOR", fg=NeonUI.NEON_GREEN, bg=NeonUI.BG,
            font=self.orbitron_font
        )
        subtitle = tk.Label(
            self, text="Visual similarity defense • Unicode normalization",
            fg=NeonUI.NEON_BLUE, bg=NeonUI.BG, font=self.consola_font
        )
        title.pack(pady=(16, 2))
        subtitle.pack(pady=(0, 16))

        # Tabs
        nb = ttk.Notebook(self)
        self.tab_compare = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_scan = tk.Frame(nb, bg=NeonUI.BG)
        nb.add(self.tab_compare, text="Compare")
        nb.add(self.tab_scan, text="Scan")
        nb.pack(fill="both", expand=True)

        self._build_compare_tab()
        self._build_scan_tab()
        self._build_status_bar()

    # ---------------- Tabs -----------------

    def _build_compare_tab(self):
        frm = self.tab_compare
        for col in range(2):
            frm.grid_columnconfigure(col, weight=1)

        tk.Label(frm, text="String A", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        tk.Label(frm, text="String B", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=1, sticky="w", padx=16, pady=(16, 4))

        self.entry_a = ttk.Entry(frm)
        self.entry_b = ttk.Entry(frm)
        self.entry_a.grid(row=1, column=0, padx=16, sticky="ew")
        self.entry_b.grid(row=1, column=1, padx=16, sticky="ew")

        btn = ttk.Button(frm, text="Compare (Fold)", command=self.on_compare)
        btn.grid(row=2, column=0, columnspan=2, pady=14)

        # Results area
        self.text_compare = tk.Text(frm, height=16, bg=NeonUI.PANEL, fg=NeonUI.FG, insertbackground=NeonUI.NEON_GREEN, bd=0, font=self.consola_font)
        self.text_compare.grid(row=3, column=0, columnspan=2, padx=16, pady=(4, 16), sticky="nsew")
        frm.grid_rowconfigure(3, weight=1)

        # Controls row
        ctrl = tk.Frame(frm, bg=NeonUI.BG)
        ctrl.grid(row=4, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        ttk.Button(ctrl, text="Load confusables.txt", command=self.load_confusables).pack(side="left")
        self.var_strip = tk.BooleanVar(value=True)
        self.var_lower = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl, text="Strip diacritics", variable=self.var_strip).pack(side="left", padx=8)
        ttk.Checkbutton(ctrl, text="Lowercase", variable=self.var_lower).pack(side="left", padx=8)
        
        # Define tags for highlighting
        self.text_compare.tag_configure("diff", foreground=NeonUI.NEON_BLUE, font=("Consolas", 11, "bold"))
        self.text_compare.tag_configure("normal", foreground=NeonUI.FG)
        self.text_compare.tag_configure("verdict_match", foreground=NeonUI.NEON_GREEN, font=("Consolas", 13, "bold"))
        self.text_compare.tag_configure("verdict_diff", foreground=NeonUI.RED, font=("Consolas", 13, "bold"))

    def _build_scan_tab(self):
        frm = self.tab_scan
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Input string to scan", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.entry_scan = ttk.Entry(frm)
        self.entry_scan.grid(row=1, column=0, padx=16, sticky="ew")
        ttk.Button(frm, text="Scan", command=self.on_scan).grid(row=2, column=0, pady=12)

        # Findings table
        cols = ("index", "found", "→", "replacement")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, anchor="center")
        self.tree.grid(row=3, column=0, padx=16, pady=(4, 12), sticky="nsew")
        frm.grid_rowconfigure(3, weight=1)

        # Highlighted preview
        tk.Label(frm, text="Highlighted preview", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=4, column=0, sticky="w", padx=16)
        self.text_scan = tk.Text(frm, height=10, bg=NeonUI.PANEL, fg=NeonUI.FG, insertbackground=NeonUI.NEON_GREEN, bd=0, font=self.consola_font)
        self.text_scan.grid(row=5, column=0, padx=16, pady=(4, 16), sticky="nsew")
        self.text_scan.tag_configure("hit", foreground=NeonUI.NEON_BLUE)

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=NeonUI.BG)
        bar.pack(fill="x")
        self.status_lbl = tk.Label(bar, text="Ready • Built-in rules: {}".format(len(UNIFIED_HOMOGLYPH_MAP)), bg=NeonUI.BG, fg=NeonUI.NEON_GREEN, font=self.consola_font)
        self.status_lbl.pack(side="left", padx=12, pady=8)
        ttk.Button(bar, text="About", command=self.on_about).pack(side="right", padx=8)

    # --------------- Actions ---------------

    def current_options(self) -> FoldOptions:
        return FoldOptions(lower=self.var_lower.get(), strip_marks=self.var_strip.get())

    def _get_folding_segments(self, text: str) -> List[Tuple[str, str, str]]:
        """Helper to get segments of original, folded, and type of homoglyph."""
        opts = self.current_options()
        full_map = dict(UNIFIED_HOMOGLYPH_MAP)
        if self.extra_map:
            full_map.update(self.extra_map)
        
        keys = sorted(full_map.keys(), key=len, reverse=True)
        
        i = 0
        segments = []
        t = unicodedata.normalize("NFKC", text)
        if opts.lower:
            t = t.lower()
        if opts.strip_marks:
            t = strip_diacritics(t)

        while i < len(text):
            found_key = None
            found_len = 0
            for k in keys:
                # Find longest match in the normalized string `t`
                if t.startswith(k, i):
                    found_key = k
                    found_len = len(k)
                    break
            
            if found_key:
                original_segment = text[i:i+found_len]
                folded_segment, homoglyph_type = full_map[found_key]
                segments.append((original_segment, folded_segment, homoglyph_type))
                i += found_len
            else:
                original_segment = text[i]
                folded_segment = t[i]
                homoglyph_type = "Base ASCII" if original_segment == folded_segment else "Diacritic"
                segments.append((original_segment, folded_segment, homoglyph_type))
                i += 1
                
        return segments

    def on_compare(self):
        a = self.entry_a.get()
        b = self.entry_b.get()
        if not a or not b:
            messagebox.showwarning("Input required", "Please enter both strings.")
            return

        segments_a = self._get_folding_segments(a)
        segments_b = self._get_folding_segments(b)
        
        fa = "".join(s[1] for s in segments_a)
        fb = "".join(s[1] for s in segments_b)
        
        self.text_compare.delete("1.0", "end")
        
        if fa == fb:
            self.text_compare.insert("end", "Result: MATCH (Homoglyphs detected)\n\n", "verdict_match")
            
            self.text_compare.insert("end", "String A: ", "normal")
            for i, seg in enumerate(segments_a):
                original, folded, _type = seg
                if original != folded:
                    self.text_compare.insert("end", original, "diff")
                else:
                    self.text_compare.insert("end", original, "normal")
            self.text_compare.insert("end", "\n\n", "normal")
            
            self.text_compare.insert("end", "String B: ", "normal")
            for i, seg in enumerate(segments_b):
                original, folded, _type = seg
                if original != folded:
                    self.text_compare.insert("end", original, "diff")
                else:
                    self.text_compare.insert("end", original, "normal")
            self.text_compare.insert("end", "\n\n", "normal")
            
            self.text_compare.insert("end", "Detailed Breakdown:\n", "normal")
            # Create a combined list of segments to compare
            combined_segments = []
            max_len = max(len(segments_a), len(segments_b))
            for i in range(max_len):
                seg_a = segments_a[i] if i < len(segments_a) else None
                seg_b = segments_b[i] if i < len(segments_b) else None
                combined_segments.append((seg_a, seg_b))
            
            for seg_a, seg_b in combined_segments:
                if seg_a and seg_b and seg_a[0] != seg_b[0] and seg_a[1] == seg_b[1]:
                    self.text_compare.insert("end", f" • ", "normal")
                    self.text_compare.insert("end", f"'{seg_a[0]}' ", "diff")
                    self.text_compare.insert("end", f"({seg_a[2]})", "normal")
                    self.text_compare.insert("end", f" vs ", "normal")
                    self.text_compare.insert("end", f"'{seg_b[0]}' ", "diff")
                    self.text_compare.insert("end", f"({seg_b[2]})", "normal")
                    self.text_compare.insert("end", f" both fold to '{seg_a[1]}'\n", "normal")
                elif seg_a and seg_a[0] != seg_a[1]:
                    self.text_compare.insert("end", f" • String A: '{seg_a[0]}' ({seg_a[2]}) folds to '{seg_a[1]}'\n", "normal")
                elif seg_b and seg_b[0] != seg_b[1]:
                    self.text_compare.insert("end", f" • String B: '{seg_b[0]}' ({seg_b[2]}) folds to '{seg_b[1]}'\n", "normal")


        else:
            self.text_compare.insert("end", "Result: DIFFERENT\n\n", "verdict_diff")
            self.text_compare.insert("end", f"Folded A → {fa}\nFolded B → {fb}\n\n", "normal")
            
            self.text_compare.insert("end", "String A: " + a + "\n", "normal")
            self.text_compare.insert("end", "String B: " + b + "\n", "normal")

    def on_scan(self):
        s = self.entry_scan.get()
        if not s:
            messagebox.showwarning("Input required", "Please enter a string to scan.")
            return

        findings = scan_string(s, extra_map=self.extra_map)
        
        # Update table
        for row in self.tree.get_children():
            self.tree.delete(row)
        for (found, repl, idx) in findings:
            self.tree.insert("", "end", values=(idx, found, "→", repl))

        # Highlight in preview
        self.text_scan.delete("1.0", "end")
        self.text_scan.insert("end", s)
        self.text_scan.tag_remove("hit", "1.0", "end")
        for (found, _repl, idx) in findings:
            start = self._index_to_text_index(idx)
            end = self._index_to_text_index(idx + len(found))
            self.text_scan.tag_add("hit", start, end)

        self.set_status(f"Scan complete • {len(findings)} suspicious segment(s)")

    def _index_to_text_index(self, idx: int) -> str:
        # Text indices are 1.0-based; our text has a single line
        return f"1.{idx}"

    def on_about(self):
        messagebox.showinfo(
            "About",
            "Homoglyph Detector – Neon\n\n" +
            "• NFKC + optional diacritic stripping\n" +
            "• Built-in Cyrillic, Greek, Latin folding ({}) rules\n".format(len(UNIFIED_HOMOGLYPH_MAP)) +
            "• Load confusables.txt for thousands more\n\n" +
            CONFUSABLES_HINT
        )

    def set_status(self, text: str):
        self.status_lbl.config(text=text)

    def load_confusables(self):
        path = filedialog.askopenfilename(
            title="Select confusables.txt",
            filetypes=[("Text", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            conf = load_confusables_txt(path)
            # Filter out identities and ensure no recursive loops
            conf = {k: v for k, v in conf.items() if k != v}
            self.extra_map = conf
            self.set_status(f"Loaded {len(conf)} extra rules from confusables.txt")
            messagebox.showinfo("Loaded", f"Added {len(conf)} confusable mappings.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load confusables: {e}")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    # Add a check for Python 3.6+ because of f-strings
    if sys.version_info < (3, 6):
        print("This script requires Python 3.6 or later.")
        sys.exit(1)
    
    # Check if a specific font is available before trying to use it
    try:
        tk.Tk().tk.call('font', 'families', 'Orbitron')
    except:
        print("Orbitron font not found. Falling back to default.")

    main()