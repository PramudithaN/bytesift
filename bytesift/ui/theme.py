"""
ByteSift Modern Cross-Platform Theme & Styling Engine
Supports Windows 11 Fluent and macOS Aqua/Human Interface Guidelines with automatic
system dark/light mode detection on Windows, macOS, and Linux.
"""

import ctypes
from dataclasses import dataclass
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple

IS_WINDOWS = sys.platform == "win32"
IS_DARWIN = sys.platform == "darwin"

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
    button_secondary_pressed: str
    entry_bg: str
    entry_border: str
    scroll_track: str
    scroll_thumb: str
    scroll_thumb_hover: str
    check_bg: str
    check_border: str
    check_indicator: str
    table_bg: str
    table_alt_bg: str
    table_selected: str
    table_selected_text: str
    table_header_bg: str
    table_header_text: str
    table_border: str
    status_bg: str
    warning_bg: str
    warning_text: str

# Windows 11 Fluent Dark & Light Palettes
WINDOWS_DARK = ThemeColors(
    name="dark",
    bg="#1a1a1a",
    card_bg="#242424",
    card_border="#333333",
    text_primary="#ffffff",
    text_secondary="#999999",
    accent="#60cdff",
    accent_hover="#7ad6ff",
    accent_text="#000000",
    button_secondary_bg="#2e2e2e",
    button_secondary_hover="#383838",
    button_secondary_pressed="#222222",
    entry_bg="#1b1b1b",
    entry_border="#3a3a3a",
    scroll_track="#1e1e1e",
    scroll_thumb="#3e3e3e",
    scroll_thumb_hover="#505050",
    check_bg="#1e1e1e",
    check_border="#555555",
    check_indicator="#60cdff",
    table_bg="#202020",
    table_alt_bg="#262626",
    table_selected="#004b80",
    table_selected_text="#ffffff",
    table_header_bg="#292929",
    table_header_text="#cccccc",
    table_border="#2d2d2d",
    status_bg="#151515",
    warning_bg="#3d2d00",
    warning_text="#ffd358"
)

WINDOWS_LIGHT = ThemeColors(
    name="light",
    bg="#f3f3f3",
    card_bg="#ffffff",
    card_border="#e0e0e0",
    text_primary="#1b1b1b",
    text_secondary="#606060",
    accent="#0067c0",
    accent_hover="#1975c5",
    accent_text="#ffffff",
    button_secondary_bg="#f5f5f5",
    button_secondary_hover="#e8e8e8",
    button_secondary_pressed="#d8d8d8",
    entry_bg="#ffffff",
    entry_border="#d0d0d0",
    scroll_track="#f0f0f0",
    scroll_thumb="#c1c1c1",
    scroll_thumb_hover="#a6a6a6",
    check_bg="#ffffff",
    check_border="#888888",
    check_indicator="#0067c0",
    table_bg="#ffffff",
    table_alt_bg="#f9f9f9",
    table_selected="#cce8ff",
    table_selected_text="#000000",
    table_header_bg="#f0f0f0",
    table_header_text="#222222",
    table_border="#e5e5e5",
    status_bg="#eaeaea",
    warning_bg="#fff4ce",
    warning_text="#7a5200"
)

# macOS Aqua & Human Interface Guidelines Palettes
MACOS_DARK = ThemeColors(
    name="dark",
    bg="#1e1e1e",
    card_bg="#282828",
    card_border="#3a3a3c",
    text_primary="#ffffff",
    text_secondary="#98989d",
    accent="#0a84ff",
    accent_hover="#409cff",
    accent_text="#ffffff",
    button_secondary_bg="#323232",
    button_secondary_hover="#3d3d3d",
    button_secondary_pressed="#262626",
    entry_bg="#1e1e1e",
    entry_border="#3a3a3c",
    scroll_track="#202020",
    scroll_thumb="#444446",
    scroll_thumb_hover="#5c5c5e",
    check_bg="#1e1e1e",
    check_border="#545458",
    check_indicator="#0a84ff",
    table_bg="#222222",
    table_alt_bg="#282828",
    table_selected="#0a84ff",
    table_selected_text="#ffffff",
    table_header_bg="#2c2c2e",
    table_header_text="#d1d1d6",
    table_border="#3a3a3c",
    status_bg="#181818",
    warning_bg="#3a2e0a",
    warning_text="#ffd60a"
)

MACOS_LIGHT = ThemeColors(
    name="light",
    bg="#f2f2f7",
    card_bg="#ffffff",
    card_border="#e5e5ea",
    text_primary="#000000",
    text_secondary="#6c6c70",
    accent="#007aff",
    accent_hover="#0062cc",
    accent_text="#ffffff",
    button_secondary_bg="#e5e5ea",
    button_secondary_hover="#d1d1d6",
    button_secondary_pressed="#c7c7cc",
    entry_bg="#ffffff",
    entry_border="#d1d1d6",
    scroll_track="#f2f2f7",
    scroll_thumb="#c7c7cc",
    scroll_thumb_hover="#aeaeb2",
    check_bg="#ffffff",
    check_border="#8e8e93",
    check_indicator="#007aff",
    table_bg="#ffffff",
    table_alt_bg="#f7f7fa",
    table_selected="#007aff",
    table_selected_text="#ffffff",
    table_header_bg="#f2f2f7",
    table_header_text="#1c1c1e",
    table_border="#e5e5ea",
    status_bg="#e5e5ea",
    warning_bg="#fff9e6",
    warning_text="#8f6b00"
)

# Active platform theme defaults
DARK_THEME = MACOS_DARK if IS_DARWIN else WINDOWS_DARK
LIGHT_THEME = MACOS_LIGHT if IS_DARWIN else WINDOWS_LIGHT

def get_system_font(size: int = 9, bold: bool = False) -> Tuple[str, int, str]:
    """Returns platform-optimized system font tuple."""
    weight = "bold" if bold else "normal"
    if IS_DARWIN:
        return (".AppleSystemUIFont", size, weight)
    if IS_WINDOWS:
        return ("Segoe UI", size, weight)
    return ("sans-serif", size, weight)

def enable_windows_dpi_awareness():
    """Configures high-DPI awareness on Windows to prevent blurry rendering."""
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
    """Reads Windows Personalize registry key to detect Dark Mode."""
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

def is_macos_dark_theme() -> bool:
    """Reads macOS user defaults to detect Dark Mode."""
    if not IS_DARWIN:
        return False
    try:
        res = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
            timeout=1
        )
        return res.returncode == 0 and "Dark" in res.stdout
    except (OSError, subprocess.SubprocessError):
        return False

def is_system_dark_theme() -> bool:
    """Detects system Dark Mode across Windows, macOS, and Linux."""
    if IS_WINDOWS:
        return is_windows_dark_theme()
    if IS_DARWIN:
        return is_macos_dark_theme()
    return False

def set_windows_titlebar_appearance(root: tk.Tk, dark: bool):
    """Sets dark mode on Windows 10/11 title bar via DwmSetWindowAttribute."""
    if not IS_WINDOWS:
        return
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if not hwnd:
            hwnd = root.winfo_id()

        val = ctypes.c_int(1 if dark else 0)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
        if res != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), ctypes.sizeof(val))
    except (AttributeError, OSError):
        pass

def apply_fluent_theme(root: tk.Tk, theme: ThemeColors):
    """Applies modern Fluent (Windows) / Aqua (macOS) styles across widgets."""
    root.configure(bg=theme.bg)
    style = ttk.Style(root)
    style.theme_use("clam")

    font_body = get_system_font(9)
    font_bold = get_system_font(9, bold=True)
    font_title = get_system_font(16, bold=True)
    font_section = get_system_font(10, bold=True)

    # Global Tk option database for popups, combobox dropdown lists, and menus
    root.option_add("*TCombobox*Listbox.background", theme.card_bg)
    root.option_add("*TCombobox*Listbox.foreground", theme.text_primary)
    root.option_add("*TCombobox*Listbox.selectBackground", theme.accent)
    root.option_add("*TCombobox*Listbox.selectForeground", theme.accent_text)
    root.option_add("*TCombobox*Listbox.font", font_body)
    root.option_add("*TCombobox*Listbox.relief", "flat")
    root.option_add("*TCombobox*Listbox.borderWidth", "1")
    root.option_add("*TCombobox*Listbox.highlightThickness", "1")
    root.option_add("*TCombobox*Listbox.highlightColor", theme.card_border)
    root.option_add("*TCombobox*Listbox.highlightBackground", theme.card_border)

    # Base Frame styles
    style.configure("TFrame", background=theme.bg)
    style.configure("Card.TFrame", background=theme.card_bg)
    style.configure("CardContent.TFrame", background=theme.card_bg)
    style.configure("Status.TFrame", background=theme.status_bg)

    # Label styles
    style.configure("TLabel", background=theme.bg, foreground=theme.text_primary, font=font_body)
    style.configure("Card.TLabel", background=theme.card_bg, foreground=theme.text_primary, font=font_body)
    style.configure("CardSecondary.TLabel", background=theme.card_bg, foreground=theme.text_secondary, font=font_body)
    style.configure("Title.TLabel", background=theme.bg, foreground=theme.text_primary, font=font_title)
    style.configure("Subtitle.TLabel", background=theme.bg, foreground=theme.text_secondary, font=font_body)
    style.configure("Section.TLabel", background=theme.card_bg, foreground=theme.text_primary, font=font_section)
    style.configure("Status.TLabel", background=theme.status_bg, foreground=theme.text_primary, font=font_body)

    # Modern Entry styling
    style.configure(
        "TEntry",
        fieldbackground=theme.entry_bg,
        foreground=theme.text_primary,
        insertcolor=theme.text_primary,
        bordercolor=theme.entry_border,
        lightcolor=theme.card_bg,
        darkcolor=theme.card_bg,
        padding=6,
        font=font_body
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", theme.accent), ("hover", theme.text_secondary)]
    )

    # Modern Checkbutton styling
    style.configure(
        "TCheckbutton",
        background=theme.card_bg,
        foreground=theme.text_primary,
        indicatorbackground=theme.check_bg,
        indicatorforeground=theme.check_indicator,
        upperbordercolor=theme.check_border,
        lowerbordercolor=theme.check_border,
        indicatorsize=15,
        indicatormargin=(0, 2, 8, 2),
        font=font_body
    )
    style.map(
        "TCheckbutton",
        background=[("active", theme.card_bg)],
        foreground=[("active", theme.text_primary)],
        indicatorbackground=[
            ("selected", theme.check_bg),
            ("active", theme.button_secondary_hover),
            ("pressed", theme.button_secondary_bg)
        ],
        indicatorforeground=[
            ("selected", theme.check_indicator),
            ("active", theme.accent_hover)
        ],
        upperbordercolor=[("selected", theme.accent), ("active", theme.accent_hover)],
        lowerbordercolor=[("selected", theme.accent), ("active", theme.accent_hover)]
    )

    # Modern Combobox styling
    style.configure(
        "TCombobox",
        fieldbackground=theme.entry_bg,
        background=theme.button_secondary_bg,
        foreground=theme.text_primary,
        arrowcolor=theme.text_primary,
        bordercolor=theme.entry_border,
        lightcolor=theme.card_bg,
        darkcolor=theme.card_bg,
        padding=5,
        font=font_body
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", theme.entry_bg), ("active", theme.entry_bg)],
        foreground=[("readonly", theme.text_primary), ("active", theme.text_primary)],
        selectbackground=[("readonly", theme.entry_bg)],
        selectforeground=[("readonly", theme.text_primary)],
        arrowcolor=[("active", theme.accent), ("pressed", theme.accent)],
        bordercolor=[("focus", theme.accent), ("active", theme.accent)]
    )

    # Modern Button styles
    # Primary Accent Button
    style.configure(
        "Accent.TButton",
        font=font_bold,
        background=theme.accent,
        foreground=theme.accent_text,
        bordercolor=theme.accent,
        lightcolor=theme.accent,
        darkcolor=theme.accent,
        relief="flat",
        padding=(16, 7)
    )
    style.map(
        "Accent.TButton",
        background=[("active", theme.accent_hover), ("disabled", theme.button_secondary_bg)],
        foreground=[("disabled", theme.text_secondary)],
        bordercolor=[("active", theme.accent_hover), ("disabled", theme.card_border)]
    )

    # Secondary Button
    style.configure(
        "TButton",
        font=font_body,
        background=theme.button_secondary_bg,
        foreground=theme.text_primary,
        bordercolor=theme.card_border,
        lightcolor=theme.button_secondary_bg,
        darkcolor=theme.button_secondary_bg,
        relief="flat",
        padding=(12, 6)
    )
    style.map(
        "TButton",
        background=[
            ("pressed", theme.button_secondary_pressed),
            ("active", theme.button_secondary_hover),
            ("disabled", theme.bg)
        ],
        foreground=[("disabled", theme.text_secondary)],
        bordercolor=[("active", theme.text_secondary), ("disabled", theme.card_border)]
    )

    # Modern Scrollbar styling
    for orient in ["Vertical", "Horizontal"]:
        style.configure(
            f"{orient}.TScrollbar",
            background=theme.scroll_thumb,
            troughcolor=theme.scroll_track,
            bordercolor=theme.scroll_track,
            arrowcolor=theme.text_secondary,
            lightcolor=theme.scroll_thumb,
            darkcolor=theme.scroll_thumb,
            arrowsize=11,
            gripcount=0,
            relief="flat"
        )
        style.map(
            f"{orient}.TScrollbar",
            background=[("active", theme.scroll_thumb_hover), ("pressed", theme.accent)],
            arrowcolor=[("active", theme.text_primary), ("pressed", theme.accent)]
        )

    # Modern Treeview (Table) styling
    style.configure(
        "Treeview",
        background=theme.table_bg,
        foreground=theme.text_primary,
        fieldbackground=theme.table_bg,
        bordercolor=theme.table_border,
        lightcolor=theme.table_bg,
        darkcolor=theme.table_bg,
        rowheight=28,
        font=font_body
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
        bordercolor=theme.table_border,
        lightcolor=theme.table_header_bg,
        darkcolor=theme.table_header_bg,
        font=font_bold,
        relief="flat",
        padding=(8, 7)
    )
    style.map(
        "Treeview.Heading",
        background=[("active", theme.button_secondary_hover)],
        foreground=[("active", theme.text_primary)]
    )

    # Update Windows Title Bar if on Windows
    if IS_WINDOWS:
        set_windows_titlebar_appearance(root, theme.name == "dark")
