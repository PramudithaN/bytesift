"""
ByteSift Modern Windows Theme & Styling Engine
Provides Windows 11 / Fluent styling with automatic system dark/light mode detection.
"""

import ctypes
from dataclasses import dataclass
import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional

# Safe check for Windows
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None

@dataclass
class ThemeColors:
    name: str
    bg: str
    card_bg: str
    card_border: str
    text_primary: str
    text_secondary: str
    accent: str
    accent_hover: str
    accent_text: str
    button_secondary_bg: str
    button_secondary_hover: str
    entry_bg: str
    entry_border: str
    table_bg: str
    table_alt_bg: str
    table_selected: str
    table_selected_text: str
    table_header_bg: str
    table_header_text: str
    status_bg: str
    warning_bg: str
    warning_text: str

DARK_THEME = ThemeColors(
    name="dark",
    bg="#202020",
    card_bg="#2b2b2b",
    card_border="#3a3a3a",
    text_primary="#ffffff",
    text_secondary="#aaaaaa",
    accent="#60cdff",
    accent_hover="#7ad6ff",
    accent_text="#000000",
    button_secondary_bg="#383838",
    button_secondary_hover="#444444",
    entry_bg="#1f1f1f",
    entry_border="#444444",
    table_bg="#242424",
    table_alt_bg="#2b2b2b",
    table_selected="#004b80",
    table_selected_text="#ffffff",
    table_header_bg="#2b2b2b",
    table_header_text="#dddddd",
    status_bg="#1a1a1a",
    warning_bg="#4d3800",
    warning_text="#ffd358"
)

LIGHT_THEME = ThemeColors(
    name="light",
    bg="#f3f3f3",
    card_bg="#ffffff",
    card_border="#e5e5e5",
    text_primary="#1b1b1b",
    text_secondary="#5f5f5f",
    accent="#0067c0",
    accent_hover="#1975c5",
    accent_text="#ffffff",
    button_secondary_bg="#e1e1e1",
    button_secondary_hover="#d5d5d5",
    entry_bg="#ffffff",
    entry_border="#d0d0d0",
    table_bg="#ffffff",
    table_alt_bg="#f9f9f9",
    table_selected="#cce8ff",
    table_selected_text="#000000",
    table_header_bg="#f0f0f0",
    table_header_text="#222222",
    status_bg="#e8e8e8",
    warning_bg="#fff4ce",
    warning_text="#7a5200"
)

def enable_windows_dpi_awareness():
    """Configures high-DPI awareness on Windows to prevent blurry text."""
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass

def is_windows_dark_theme() -> bool:
    """Reads the Windows Personalize registry key to detect system dark mode."""
    if not IS_WINDOWS or not winreg:
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return val == 0
    except (OSError, FileNotFoundError):
        return False

def set_windows_titlebar_appearance(root: tk.Tk, dark: bool):
    """Sets immersive dark mode on Windows 10/11 title bar via DwmSetWindowAttribute."""
    if not IS_WINDOWS:
        return
    try:
        root.update_idletasks()
        # Retrieve HWND of window
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if not hwnd:
            hwnd = root.winfo_id()

        # DWMWA_USE_IMMERSIVE_DARK_MODE attribute (20 for Win11/Win10 20H1+, 19 for earlier)
        val = ctypes.c_int(1 if dark else 0)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
        if res != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), ctypes.sizeof(val))
    except (AttributeError, OSError):
        pass

def apply_fluent_theme(root: tk.Tk, theme: ThemeColors):
    """Applies modern Windows Fluent theme styles across all TTK widgets."""
    root.configure(bg=theme.bg)
    style = ttk.Style(root)
    style.theme_use("clam")

    # Frame styles
    style.configure("TFrame", background=theme.bg)
    style.configure("Card.TFrame", background=theme.card_bg, relief="solid", borderwidth=1)
    style.configure("CardContent.TFrame", background=theme.card_bg)
    style.configure("Status.TFrame", background=theme.status_bg)

    # Label styles
    style.configure(
        "TLabel",
        background=theme.bg,
        foreground=theme.text_primary,
        font=("Segoe UI", 9)
    )
    style.configure(
        "Card.TLabel",
        background=theme.card_bg,
        foreground=theme.text_primary,
        font=("Segoe UI", 9)
    )
    style.configure(
        "CardSecondary.TLabel",
        background=theme.card_bg,
        foreground=theme.text_secondary,
        font=("Segoe UI", 9)
    )
    style.configure(
        "Title.TLabel",
        background=theme.bg,
        foreground=theme.text_primary,
        font=("Segoe UI", 16, "bold")
    )
    style.configure(
        "Subtitle.TLabel",
        background=theme.bg,
        foreground=theme.text_secondary,
        font=("Segoe UI", 9)
    )
    style.configure(
        "Section.TLabel",
        background=theme.card_bg,
        foreground=theme.text_primary,
        font=("Segoe UI", 10, "bold")
    )
    style.configure(
        "Status.TLabel",
        background=theme.status_bg,
        foreground=theme.text_primary,
        font=("Segoe UI", 9)
    )

    # Button Styles
    # 1. Accent Primary Button (e.g. Organize)
    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 9, "bold"),
        background=theme.accent,
        foreground=theme.accent_text,
        borderwidth=0,
        focuscolor=theme.accent,
        padding=(14, 6)
    )
    style.map(
        "Accent.TButton",
        background=[("active", theme.accent_hover), ("disabled", theme.card_border)],
        foreground=[("disabled", theme.text_secondary)]
    )

    # 2. Standard Secondary Button
    style.configure(
        "TButton",
        font=("Segoe UI", 9),
        background=theme.button_secondary_bg,
        foreground=theme.text_primary,
        borderwidth=0,
        padding=(12, 5)
    )
    style.map(
        "TButton",
        background=[("active", theme.button_secondary_hover), ("disabled", theme.bg)],
        foreground=[("disabled", theme.text_secondary)]
    )

    # Entry Style
    style.configure(
        "TEntry",
        fieldbackground=theme.entry_bg,
        foreground=theme.text_primary,
        insertcolor=theme.text_primary,
        borderwidth=1,
        padding=5
    )

    # Checkbutton Style
    style.configure(
        "TCheckbutton",
        background=theme.card_bg,
        foreground=theme.text_primary,
        font=("Segoe UI", 9)
    )
    style.map(
        "TCheckbutton",
        background=[("active", theme.card_bg)],
        foreground=[("active", theme.text_primary)]
    )

    # Combobox Style
    style.configure(
        "TCombobox",
        fieldbackground=theme.entry_bg,
        background=theme.button_secondary_bg,
        foreground=theme.text_primary,
        arrowcolor=theme.text_primary,
        padding=4
    )

    # Treeview (Table)
    style.configure(
        "Treeview",
        background=theme.table_bg,
        foreground=theme.text_primary,
        fieldbackground=theme.table_bg,
        rowheight=28,
        font=("Segoe UI", 9),
        borderwidth=0
    )
    style.map(
        "Treeview",
        background=[("selected", theme.table_selected)],
        foreground=[("selected", theme.table_selected_text)]
    )
    style.configure(
        "Treeview.Heading",
        background=theme.table_header_bg,
        foreground=theme.table_header_text,
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        padding=(6, 6)
    )
    style.map(
        "Treeview.Heading",
        background=[("active", theme.button_secondary_hover)]
    )

    # Scrollbar
    style.configure(
        "Vertical.TScrollbar",
        background=theme.bg,
        troughcolor=theme.card_bg,
        borderwidth=0,
        arrowsize=12
    )

    # Update Title bar
    set_windows_titlebar_appearance(root, theme.name == "dark")
