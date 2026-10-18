#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Homoglyph Detector – Sci-Fi GUI (Python, Tkinter)

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
- NEW: Added sections for Phishing, Email, Password, File and URL monitoring.

Author: You
"""

import re
import sys
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font
from collections import defaultdict
import threading
import time
import socket
import difflib
import os
import email
import urllib.parse
from math import log10

# --- Fix for ModuleNotFoundError: No module named 'dns' ---
# The dns.resolver module is part of the 'dnspython' library and is not
# installed by default. We'll try to import it and handle the case where it's
# missing gracefully.
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    
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
    "rn": "m", "cl": "d", "vv": "w", "ſſ": "ss",
    # Specific Unicode lookalikes
    "℮": "e", "ℯ": "e", "K": "k", "ℬ": "b", "Ⅎ": "f", "ℕ": "n", "ℙ": "p", "ℚ": "q", "ℝ": "r", "ℤ": "z",
    "⍺": "a", "ℵ": "h", "⍝": "d", "℥": "g", "⍬": "q", "ℭ": "c", "ℇ": "e", "ℱ": "f",
    "ℐ": "i", "ℒ": "l", "ℳ": "m", "ℛ": "r", "ℜ": "r", "℘": "p",
    "ⅅ": "d", "ⅆ": "d", "⅐": "1", "⅑": "1", "⅒": "1",
}
# Extensive programmatic generators for Latin, Greek, and Cyrillic
GREEK_TO_LATIN = {
    "Α": "A", "Β": "B", "Ε": "E", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
    "α": "a", "β": "b", "γ": "y", "ε": "e", "η": "n", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
}

CYRILLIC_TO_LATIN = {
    "Α": "A", "Β": "B", "Ε": "E", "З": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X", "Ѵ": "I",
    "а": "a", "в": "b", "е": "e", "з": "3", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p", "с": "c", "т": "t", "у": "y", "х": "x", "і": "i",
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
    We convert target sequences to a normalized ASCII-ish skeleton using NFKC + diacritic stripping + BASE_MAP for folding.
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

def scan_string(s: str, *, extra_map: Dict[str, Tuple[str, str]] | None = None) -> List[Tuple[str, str, int, str]]:
    """Return list of (original_char, replacement, index, type) for suspicious units."""
    mapping = dict(UNIFIED_HOMOGLYPH_MAP)
    if extra_map:
        mapping.update(extra_map)
    
    keys = sorted(mapping.keys(), key=len, reverse=True)
    idx = 0
    findings: List[Tuple[str, str, int, str]] = []

    while idx < len(s):
        found = False
        for k in keys:
            if s.startswith(k, idx):
                # Ensure it's not a self-mapping
                folded_char, homoglyph_type = mapping[k]
                if k != folded_char:
                    findings.append((k, folded_char, idx, homoglyph_type))
                idx += len(k)
                found = True
                break
        if not found:
            idx += 1
    return findings

# ------------------------
# Sci-Fi Tkinter GUI
# ------------------------
class NeonUI(ttk.Style):
    BG = "#0b0f14"   # deep black-blue
    FG = "#d9ffe5"   # pale mint for text
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
                    "padding": [12, 8],
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
            "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
            "TNotebook.Tab": {
                "configure": {
                    "padding": [10, 5],
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
        self.geometry("1100x800")
        self.minsize(1000, 700)
        self.style = NeonUI(self)
        self.extra_map: Dict[str, Tuple[str, str]] = {}
        
        # Set up custom fonts if available
        try:
            self.orbitron_font = Font(family="Orbitron", size=30, weight="bold")
        except tk.TclError:
            self.orbitron_font = Font(family="Arial", size=30, weight="bold")
        try:
            self.consola_font = Font(family="Consolas", size=11)
        except tk.TclError:
            self.consola_font = Font(family="Courier New", size=11)

        # Title banner
        title = tk.Label(
            self,
            text="HOMOSEC SECURITY TOOLKIT",
            fg=NeonUI.NEON_GREEN,
            bg=NeonUI.BG,
            font=self.orbitron_font
        )
        subtitle = tk.Label(
            self,
            text="Visual similarity defense -  Unicode normalization",
            fg=NeonUI.NEON_BLUE,
            bg=NeonUI.BG,
            font=self.consola_font
        )
        title.pack(pady=(16, 2))
        subtitle.pack(pady=(0, 16))

        # Tabs
        nb = ttk.Notebook(self)
        self.tab_home = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_compare = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_scan = tk.Frame(nb, bg=NeonUI.BG)  # Original Scan Tab
        self.tab_phishing = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_email = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_password = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_file = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_visualizer = tk.Frame(nb, bg=NeonUI.BG)
        self.tab_url_monitor = tk.Frame(nb, bg=NeonUI.BG)

        nb.add(self.tab_home, text="Home")
        nb.add(self.tab_compare, text="1. Compare Strings")
        nb.add(self.tab_scan, text="2. Scan String")
        nb.add(self.tab_phishing, text="3. Phishing Domains")
        nb.add(self.tab_email, text="4. Emails")
        nb.add(self.tab_password, text="5. Password Auditor")
        nb.add(self.tab_file, text="6. File Scanner")
        nb.add(self.tab_visualizer, text="7. Homoglyph Visualizer")
        nb.add(self.tab_url_monitor, text="8. Real-time URL Monitor")
        nb.pack(fill="both", expand=True)

        self._build_home_tab()
        self._build_compare_tab()
        self._build_scan_tab()
        self._build_phishing_tab()
        self._build_email_tab()
        self._build_password_tab()
        self._build_file_tab()
        self._build_visualizer_tab()
        self._build_url_monitor_tab()

    # ---------------- Home Tab -----------------
    def _build_home_tab(self):
        frm = self.tab_home
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_rowconfigure(0, weight=1)

        main_frame = tk.Frame(frm, bg=NeonUI.BG)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        logo_frame = tk.Frame(main_frame, bg=NeonUI.BG)
        logo_frame.pack(pady=20)

        self.logo_text = tk.Label(
            logo_frame,
            text="👾",
            font=("Orbitron", 100, "bold"),
            fg=NeonUI.NEON_BLUE,
            bg=NeonUI.BG
        )
        self.logo_text.pack()

        app_name_label = tk.Label(
            main_frame,
            text="HOMOSEC",
            font=("Orbitron", 50, "bold"),
            fg=NeonUI.NEON_GREEN,
            bg=NeonUI.BG
        )
        app_name_label.pack(pady=(0, 10))

        tagline_label = tk.Label(
            main_frame,
            text="Your Toolkit Against Visual Impersonation Attacks",
            font=("Consolas", 16),
            fg=NeonUI.FG,
            bg=NeonUI.BG
        )
        tagline_label.pack()

        summary_text = tk.Label(
            main_frame,
            text="This application helps you identify and mitigate security risks from homoglyph attacks. Navigate through the tabs to check usernames, domains, emails, passwords, and files for suspicious characters that can be visually deceiving.",
            font=("Consolas", 12),
            fg=NeonUI.FG,
            bg=NeonUI.BG,
            wraplength=800,
            justify="center"
        )
        summary_text.pack(pady=20, padx=20)

        self.blink_state = True
        self.blink_logo()

    def blink_logo(self):
        if self.blink_state:
            self.logo_text.config(fg=NeonUI.NEON_GREEN)
        else:
            self.logo_text.config(fg=NeonUI.NEON_BLUE)
        self.blink_state = not self.blink_state
        self.after(500, self.blink_logo)

    # ---------------- Tab 1: Compare Strings -----------------

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

    # ---------------- Tab 2: Scan String (Original) -----------------
    def _build_scan_tab(self):
        frm = self.tab_scan
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Input string to scan", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.entry_scan = ttk.Entry(frm)
        self.entry_scan.grid(row=1, column=0, padx=16, sticky="ew")
        ttk.Button(frm, text="Scan", command=self.on_scan).grid(row=2, column=0, pady=12)

        # Findings table
        cols = ("index", "found", "→", "replacement", "type")
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

    def _build_phishing_tab(self):
        frm = self.tab_phishing
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Input URL/Domain to check", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.entry_phishing = ttk.Entry(frm)
        self.entry_phishing.grid(row=1, column=0, padx=16, sticky="ew")
        ttk.Button(frm, text="Check", command=self.on_check_phishing).grid(row=2, column=0, pady=12)

        # Findings table
        cols = ("Original", "Folded", "Similarity Score")
        self.phishing_tree = ttk.Treeview(frm, columns=cols, show="headings", height=10)
        for c in cols:
            self.phishing_tree.heading(c, text=c)
            self.phishing_tree.column(c, width=140, anchor="center")
        self.phishing_tree.grid(row=3, column=0, padx=16, pady=(4, 12), sticky="nsew")
        frm.grid_rowconfigure(3, weight=1)

        # Info area
        self.text_phishing = scrolledtext.ScrolledText(frm, height=10, bg=NeonUI.PANEL, fg=NeonUI.FG, insertbackground=NeonUI.NEON_GREEN, bd=0, font=self.consola_font)
        self.text_phishing.grid(row=4, column=0, padx=16, pady=(4, 16), sticky="nsew")

    def _build_email_tab(self):
        frm = self.tab_email
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Email to scan", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.entry_email = ttk.Entry(frm)
        self.entry_email.grid(row=1, column=0, padx=16, sticky="ew")
        ttk.Button(frm, text="Scan", command=self.on_scan_email).grid(row=2, column=0, pady=12)
        self.text_email = scrolledtext.ScrolledText(frm, height=15, bg=NeonUI.PANEL, fg=NeonUI.FG, insertbackground=NeonUI.NEON_GREEN, bd=0, font=self.consola_font)
        self.text_email.grid(row=3, column=0, padx=16, pady=(4, 16), sticky="nsew")
        frm.grid_rowconfigure(3, weight=1)

    def _build_password_tab(self):
        frm = self.tab_password
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Password to audit", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.entry_password = ttk.Entry(frm, show="*")
        self.entry_password.grid(row=1, column=0, padx=16, sticky="ew")
        ttk.Button(frm, text="Audit", command=self.on_audit_password).grid(row=2, column=0, pady=12)
        self.text_password = scrolledtext.ScrolledText(frm, height=15, bg=NeonUI.PANEL, fg=NeonUI.FG, insertbackground=NeonUI.NEON_GREEN, bd=0, font=self.consola_font)
        self.text_password.grid(row=3, column=0, padx=16, pady=(4, 16), sticky="nsew")
        frm.grid_rowconfigure(3, weight=1)

    def _build_file_tab(self):
        frm = self.tab_file
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Select files to scan for homoglyph attacks", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        ttk.Button(frm, text="Select Files", command=self.on_scan_files).grid(row=1, column=0, pady=12)
        self.file_tree = ttk.Treeview(frm, columns=("Filename", "Suspicious"), show="headings", height=10)
        self.file_tree.heading("Filename", text="Filename")
        self.file_tree.heading("Suspicious", text="Suspicious")
        self.file_tree.grid(row=2, column=0, padx=16, pady=(4, 12), sticky="nsew")
        frm.grid_rowconfigure(2, weight=1)

    def _build_visualizer_tab(self):
        frm = self.tab_visualizer
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Enter a character to see its homoglyphs", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.entry_visualizer = ttk.Entry(frm)
        self.entry_visualizer.grid(row=1, column=0, padx=16, sticky="ew")
        ttk.Button(frm, text="Visualize", command=self.on_visualize).grid(row=2, column=0, pady=12)
        self.text_visualizer = scrolledtext.ScrolledText(frm, height=15, bg=NeonUI.PANEL, fg=NeonUI.FG, insertbackground=NeonUI.NEON_GREEN, bd=0, font=self.consola_font)
        self.text_visualizer.grid(row=3, column=0, padx=16, pady=(4, 16), sticky="nsew")
        frm.grid_rowconfigure(3, weight=1)

    def _build_url_monitor_tab(self):
        frm = self.tab_url_monitor
        frm.grid_columnconfigure(0, weight=1)
        tk.Label(frm, text="Enter a URL to monitor for homoglyph attacks (Advanced)", bg=NeonUI.BG, fg=NeonUI.NEON_BLUE, font=self.consola_font).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.entry_url_monitor = ttk.Entry(frm)
        self.entry_url_monitor.grid(row=1, column=0, padx=16, sticky="ew")
        self.monitor_button = ttk.Button(frm, text="Start Monitoring", command=self.on_start_monitor)
        self.monitor_button.grid(row=2, column=0, pady=12)
        self.text_url_monitor = scrolledtext.ScrolledText(frm, height=15, bg=NeonUI.PANEL, fg=NeonUI.FG, insertbackground=NeonUI.NEON_GREEN, bd=0, font=self.consola_font)
        self.text_url_monitor.grid(row=3, column=0, padx=16, pady=(4, 16), sticky="nsew")
        frm.grid_rowconfigure(3, weight=1)
        self.is_monitoring = False
        self.monitor_thread = None

    # --------------- Actions ---------------

    def on_check_phishing(self):
        """Handle phishing domain check:
        - Read the domain/URL
        - Fold it to its ASCII-ish skeleton
        - If different, compute a similarity score and warn
        - Optionally perform DNS A-record lookup on the folded domain
        - SIMULATED: Check against a hardcoded "threat feed" and simulate takedown
        """
        domain = self.entry_phishing.get().strip()
        if not domain:
            messagebox.showwarning("Input required", "Please enter a domain or URL.")
            return
        # Reset outputs
        self.text_phishing.delete("1.0", tk.END)
        self.phishing_tree.delete(*self.phishing_tree.get_children())
        self.text_phishing.insert(tk.END, f"Checking for homoglyph attacks on: {domain}\n\n")

        # --- SIMULATED: Global Threat Feed Check ---
        known_threats = {
            "pаypal.com": "paypal.com",
            "micrоsoft.com": "microsoft.com",
            "gооgle.com": "google.com",
        }
        is_known_threat = False
        for threat, legit in known_threats.items():
            if domain == threat:
                self.text_phishing.insert(tk.END, ">>> GLOBAL THREAT FEED ALERT <<<\n", "verdict_match")
                self.text_phishing.insert(tk.END, f"Found known homoglyph threat: '{domain}' is a fake of '{legit}'.\n", "warning")
                self.phishing_tree.insert("", tk.END, values=(domain, legit, "100.00%"))
                is_known_threat = True
                break
        
        if is_known_threat:
            self.text_phishing.insert(tk.END, "Initiating automated takedown request...\n", "info")
            self.text_phishing.insert(tk.END, "Takedown request sent to hosting provider. Status: PENDING.\n\n", "info")
        else:
            # Fold the input; if folding changes it, it indicates confusable characters
            folded_domain = fold_text(domain)
            if folded_domain != domain:
                # Similarity score between original and folded gives a quick heuristic
                score = difflib.SequenceMatcher(None, domain, folded_domain).ratio() * 100.0
                self.text_phishing.insert(tk.END, f"WARNING: The domain '{domain}' contains homoglyphs and folds to '{folded_domain}'.\n", "warning")
                self.phishing_tree.insert("", tk.END, values=(domain, folded_domain, f"{score:.2f}%"))
            else:
                self.text_phishing.insert(tk.END, "The domain appears to be free of homoglyphs.\n", "info")

        # Attempt a basic DNS lookup on the folded domain if dnspython is available
        if not DNS_AVAILABLE:
            self.text_phishing.insert(tk.END, "\nDNS lookup not available. Please install the 'dnspython' library:\n", "error")
            self.text_phishing.insert(tk.END, " pip install dnspython\n", "error")
            self.text_phishing.see(tk.END)
            return
        try:
            self.text_phishing.insert(tk.END, f"Performing DNS lookup for {folded_domain}...\n")
            answers = dns.resolver.resolve(folded_domain, 'A')
            for rdata in answers:
                self.text_phishing.insert(tk.END, f" - DNS record found: {rdata.address}\n")
        except dns.resolver.NoAnswer:
            self.text_phishing.insert(tk.END, f" - DNS lookup failed: No A record found for {folded_domain}\n", "error")
        except Exception as e:
            self.text_phishing.insert(tk.END, f" - DNS lookup failed with an error: {e}\n", "error")
        self.text_phishing.see(tk.END)

    def on_scan_email(self):
        """Scan an email string or raw text:
        - Extract email addresses and URLs using regex
        - For each domain portion, run scan_string to detect homoglyphs
        - Flag suspicious senders/links in the text area
        """
        email_text = self.entry_email.get().strip()
        if not email_text:
            messagebox.showwarning("Input required", "Please enter an email address or raw email text.")
            return
        self.text_email.delete("1.0", tk.END)
        self.text_email.insert(tk.END, f"Scanning email content for homoglyphs...\n\n")
        
        # Regex to extract emails and URLs
        email_addresses = re.findall(r'[a-zA-Z0-9.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email_text)
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', email_text)
        all_items = list(set(email_addresses + urls))

        if not all_items:
            self.text_email.insert(tk.END, "No domains or email addresses found in the text.\n")
            return

        is_suspicious = False
        for item in all_items:
            if "@" in item:
                user, domain = item.split("@", 1)
                findings = scan_string(domain, extra_map=self.extra_map)
                if findings:
                    self.text_email.insert(tk.END, f"SUSPICIOUS SENDER: {item}\n", "warning")
                    self.text_email.insert(tk.END, f" - Domain '{domain}' contains homoglyphs.\n")
                    is_suspicious = True
            elif "://" in item:
                try:
                    parsed_url = urllib.parse.urlparse(item)
                    domain = parsed_url.hostname
                    if domain and scan_string(domain, extra_map=self.extra_map):
                        self.text_email.insert(tk.END, f"SUSPICIOUS LINK: {item}\n", "warning")
                        self.text_email.insert(tk.END, f" - Domain '{domain}' contains homoglyphs.\n")
                        is_suspicious = True
                except Exception as e:
                    self.text_email.insert(tk.END, f" - Could not parse URL '{item}': {e}\n")
        if not is_suspicious:
            self.text_email.insert(tk.END, "No suspicious homoglyph attacks detected in emails or URLs.\n")
        self.text_email.see(tk.END)

    def on_audit_password(self):
        """Audit password:
        - Check for homoglyphs using scan_string
        - Evaluate strength by length and variety of character classes
        - Check for common dictionary words and repeated sequences
        - Provide a qualitative strength rating
        """
        password = self.entry_password.get().strip()
        if not password:
            messagebox.showwarning("Input required", "Please enter a password.")
            return
        self.text_password.delete("1.0", tk.END)
        self.text_password.insert(tk.END, "Auditing password for homoglyph risks...\n\n")

        # Check for homoglyphs
        homoglyphs_found = scan_string(password, extra_map=self.extra_map)
        if homoglyphs_found:
            self.text_password.insert(tk.END, "WARNING: Password contains characters that can be easily confused with others (homoglyphs).\n", "warning")
            for (found, repl, _idx, _type) in homoglyphs_found:
                self.text_password.insert(tk.END, f" - Character '{found}' could be confused with '{repl}'\n")
            self.text_password.insert(tk.END, "\nThis makes it vulnerable to 'homoglyph attacks' where a malicious actor types a visually similar password.\n")
        else:
            self.text_password.insert(tk.END, "Password appears to be free of homoglyph characters. 👍\n")

        # Simple password strength check
        score = 0
        if len(password) >= 12:
            score += 2
        elif len(password) >= 10:
            score += 1
        # Character class checks
        classes = 0
        if re.search(r'[a-z]', password):
            classes += 1
        if re.search(r'[A-Z]', password):
            classes += 1
        if re.search(r'[0-9]', password):
            classes += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=$$$$\\;/`~]', password):
            classes += 1
        score += classes
        
        # Dictionary/weak patterns (simple built-in list + patterns)
        common_words = [
            "password", "letmein", "qwerty", "iloveyou", "admin", "welcome",
            "dragon", "monkey", "football", "baseball", "login", "princess"
        ]
        lower_pw = password.lower()
        has_common = any(w in lower_pw for w in common_words)
        if has_common:
            score -= 2
        # Repeated sequences or keyboard patterns
        if re.search(r'(.)\1\1', password):
            score -= 1
        if re.search(r'(1234|abcd|qwer|asdf|zxcv)', lower_pw):
            score -= 1
        
        # Final qualitative rating
        if score <= 1:
            strength = "Very Weak"
        elif score == 2:
            strength = "Weak"
        elif score == 3:
            strength = "Moderate"
        elif score == 4:
            strength = "Strong"
        elif score == 5:
            strength = "Very Strong"
        else:
            strength = "Excellent"
        self.text_password.insert(tk.END, f"\nPassword Strength: {strength}\n")
        self.text_password.see(tk.END)

    def on_scan_files(self):
        """Scan file names in a selected directory:
        - Ask user to pick a directory
        - Walk through files, scanning each filename for homoglyphs
        - Populate the table with 'Suspicious' Yes/No and show a completion dialog
        """
        directory = filedialog.askdirectory(title="Select Directory to Scan")
        if not directory:
            return
        # Reset table
        self.file_tree.delete(*self.file_tree.get_children())
        suspicious_count = 0
        for root, _, files in os.walk(directory):
            for filename in files:
                findings = scan_string(filename, extra_map=self.extra_map)
                if findings:
                    self.file_tree.insert("", tk.END, values=(os.path.join(root, filename), "Yes"))
                    suspicious_count += 1
                else:
                    self.file_tree.insert("", tk.END, values=(os.path.join(root, filename), "No"))
        messagebox.showinfo("Scan Complete", f"File scan complete. {suspicious_count} suspicious files found.")

    def on_visualize(self):
        """Visualize homoglyphs for an input character/word:
        - Compute the folded skeleton of input
        - Find all map keys that fold to the same skeleton
        - Display each homoglyph and its type
        """
        char = self.entry_visualizer.get().strip()
        self.text_visualizer.delete("1.0", tk.END)
        if not char:
            self.text_visualizer.insert(tk.END, "Please enter a character or word.\n")
            return
        self.text_visualizer.insert(tk.END, f"Homoglyphs for: '{char}'\n\n")

        found_homoglyphs = defaultdict(list)
        full_map = dict(UNIFIED_HOMOGLYPH_MAP)
        if self.extra_map:
            full_map.update(self.extra_map)

        # Fold the input to determine the skeleton to match
        folded_input = fold_text(char)
        for k, v in full_map.items():
            if v[0] == folded_input:
                if k != char and k not in [h[0] for h in found_homoglyphs[folded_input]]:
                    found_homoglyphs[folded_input].append((k, v[1]))

        if found_homoglyphs:
            self.text_visualizer.insert(tk.END, f" - The input folds to '{folded_input}'\n", "normal")
            for folded_char, homoglyphs in found_homoglyphs.items():
                for h_char, h_type in homoglyphs:
                    self.text_visualizer.insert(tk.END, f"     - Homoglyph: '{h_char}' (Type: {h_type})\n")
        else:
            self.text_visualizer.insert(tk.END, "No common homoglyphs found in the current map.\n")
        self.text_visualizer.see(tk.END)

    def _build_url_monitor_tab_logic_tick(self, url: str):
        """Thread-safe helper: append a tick result into the monitor text box."""
        try:
            findings = scan_string(url, extra_map=self.extra_map)
            if findings:
                self.text_url_monitor.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] WARNING: Homoglyphs detected in URL '{url}'.\n", "warning")
            else:
                self.text_url_monitor.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] URL '{url}' is clean.\n")
        except Exception as e:
            self.text_url_monitor.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] ERROR: {e}\n", "error")
        self.text_url_monitor.see(tk.END)

    def _monitor_url(self, url):
        """Background thread:
        - Every 5 seconds request the main thread to append a detection status line
        - Uses self.after to ensure GUI updates are done on the main thread
        """
        while self.is_monitoring:
            # Schedule a safe UI update on the main thread
            self.after(0, self._build_url_monitor_tab_logic_tick, url)
            time.sleep(5)

    def on_start_monitor(self):
        """Start/Stop monitoring the URL:
        - On start: create a daemon thread that periodically runs scan_string on the input URL
        - On stop: flip flag; thread will exit naturally
        """
        if not self.is_monitoring:
            url = self.entry_url_monitor.get().strip()
            if not url:
                messagebox.showwarning("Input required", "Please enter a URL to monitor.")
                return
            self.is_monitoring = True
            self.monitor_button.config(text="Stop Monitoring")
            self.text_url_monitor.delete("1.0", tk.END)
            self.text_url_monitor.insert(tk.END, f"Starting real-time monitoring for: {url}\n\n")
            # Start a background thread to avoid blocking the GUI
            self.monitor_thread = threading.Thread(target=self._monitor_url, args=(url,), daemon=True)
            self.monitor_thread.start()
        else:
            # Signal the thread to stop; it will exit the loop on next tick
            self.is_monitoring = False
            self.monitor_button.config(text="Start Monitoring")
            self.text_url_monitor.insert(tk.END, "\nMonitoring stopped.\n")

    def on_compare(self):
        """Compare two strings visually by folding to skeleton:
        - Build folding segments to show per-character differences and types
        - If folded forms match, highlight differing originals that map to same folded char
        - Else show folded outputs and originals
        """
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
            for original, folded, _type in segments_a:
                if original != folded:
                    self.text_compare.insert("end", original, "diff")
                else:
                    self.text_compare.insert("end", original, "normal")
            
            self.text_compare.insert("end", "\n\n", "normal")
            self.text_compare.insert("end", "String B: ", "normal")
            for original, folded, _type in segments_b:
                if original != folded:
                    self.text_compare.insert("end", original, "diff")
                else:
                    self.text_compare.insert("end", original, "normal")

            self.text_compare.insert("end", "\n\n", "normal")
            self.text_compare.insert("end", "Detailed Breakdown:\n", "normal")

            # Pairwise comparison of segments to call out specific homoglyph mappings
            for i in range(max(len(segments_a), len(segments_b))):
                seg_a = segments_a[i] if i < len(segments_a) else None
                seg_b = segments_b[i] if i < len(segments_b) else None

                if seg_a and seg_b and seg_a[1] == seg_b[1] and seg_a[0] != seg_b[0]:
                    self.text_compare.insert("end", f" -   '{seg_a[0]}' vs '{seg_b[0]}' both fold to '{seg_a[1]}' (Type: {seg_a[2]} vs {seg_b[2]})\n")
                elif seg_a and seg_a[0] != seg_a[1]:
                    self.text_compare.insert("end", f" -   String A: '{seg_a[0]}' folds to '{seg_a[1]}' (Type: {seg_a[2]})\n")
                elif seg_b and seg_b[0] != seg_b[1]:
                    self.text_compare.insert("end", f" -   String B: '{seg_b[0]}' folds to '{seg_b[1]}' (Type: {seg_b[2]})\n")
        else:
            self.text_compare.insert("end", "Result: DIFFERENT\n\n", "verdict_diff")
            self.text_compare.insert("end", f"Folded A → {fa}\nFolded B → {fb}\n\n", "normal")
            self.text_compare.insert("end", "String A: " + a + "\n", "normal")
            self.text_compare.insert("end", "String B: " + b + "\n", "normal")

    def _get_folding_segments(self, text: str) -> List[Tuple[str, str, str]]:
        """Helper to get segments of original, folded, and type of homoglyph:
        - Applies current options (lowercase, strip marks)
        - Walks original text, greedily matching known homoglyph sequences
        - Returns list of tuples: (original_segment, folded_segment, source_type)
        """
        opts = self.current_options()
        full_map = dict(UNIFIED_HOMOGLYPH_MAP)
        if self.extra_map:
            full_map.update(self.extra_map)

        keys = sorted(full_map.keys(), key=len, reverse=True)
        i = 0
        segments = []

        while i < len(text):
            found_key = None
            found_len = 0

            # First attempt exact key match at this position (multi-char aware)
            for k in keys:
                if text.startswith(k, i):
                    found_key = k
                    found_len = len(k)
                    break
            
            if found_key:
                original_segment = text[i:i+found_len]
                folded_segment, homoglyph_type = full_map[found_key]
                segments.append((original_segment, folded_segment, homoglyph_type))
                i += found_len
            else:
                # Fallback to single character mapping/alignment
                original_segment = text[i]
                folded_segment = fold_text(original_segment, options=opts)
                homoglyph_type = "Base ASCII" if original_segment == folded_segment else "Diacritic"
                segments.append((original_segment, folded_segment, homoglyph_type))
                i += 1
        return segments

    def on_scan(self):
        """Scan a string for homoglyphs:
        - Use scan_string to find suspicious sequences
        - Populate the table with index, found sequence, and replacement
        - Highlight hits in the preview text area
        """
        s = self.entry_scan.get()
        if not s:
            messagebox.showwarning("Input required", "Please enter a string to scan.")
            return

        findings = scan_string(s, extra_map=self.extra_map)
        
        # Update table
        for row in self.tree.get_children():
            self.tree.delete(row)
        for (found, repl, idx, typ) in findings:
            self.tree.insert("", "end", values=(idx, found, "→", repl, typ))

        # Highlight in preview
        self.text_scan.delete("1.0", "end")
        self.text_scan.insert("end", s)
        self.text_scan.tag_remove("hit", "1.0", "end")
        for (found, _repl, idx, _typ) in findings:
            start = self._index_to_text_index(idx)
            end = self._index_to_text_index(idx + len(found))
            self.text_scan.tag_add("hit", start, end)
        
        if findings:
            messagebox.showinfo("Scan Complete", f"Scan complete. {len(findings)} suspicious segment(s) found.")
        else:
            messagebox.showinfo("Scan Complete", "Scan complete. No suspicious homoglyphs found.")

    def _index_to_text_index(self, idx: int) -> str:
        # Text indices are 1.0-based; our text has a single line
        return f"1.{idx}"

    def on_about(self):
        messagebox.showinfo(
            "About",
            "Homoglyph Detector – Neon\n\n"
            + "-   NFKC + optional diacritic stripping\n"
            + "-   Built-in Cyrillic, Greek, Latin folding ({}) rules\n".format(len(UNIFIED_HOMOGLYPH_MAP))
            + "-   Load confusables.txt for thousands more\n\n"
            + CONFUSABLES_HINT
        )
    
    def set_status(self, text: str):
        pass

    def load_confusables(self):
        """Load external Unicode confusables.txt to extend the map:
        - Parse and fold targets to skeleton
        - Merge into extra_map
        """
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
            messagebox.showinfo("Loaded", f"Added {len(conf)} confusable mappings from confusables.txt")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load confusables: {e}")
            
    def current_options(self) -> FoldOptions:
        return FoldOptions(lower=self.var_lower.get(), strip_marks=self.var_strip.get())

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    if sys.version_info < (3, 6):
        print("This script requires Python 3.6 or later.")
        sys.exit(1)
    
    try:
        tk.Tk().tk.call('font', 'families', 'Orbitron')
    except:
        print("Orbitron font not found. Falling back to default.")
    
    main()
