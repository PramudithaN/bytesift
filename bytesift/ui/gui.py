"""
ByteSift Modern Windows Desktop GUI
Engineered for Windows 10/11 with Fluent cards, High-DPI support, and automatic system theme detection.
"""

import ctypes
from pathlib import Path
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional
import webbrowser

from bytesift import __version__
from bytesift.core.organizer import Organizer, OrganizerConfig, PlanItem
from bytesift.core.transaction import TransactionManager
from bytesift.core.updater import UpdateInfo, check_for_updates
from bytesift.ui.theme import (
    DARK_THEME,
    LIGHT_THEME,
    MACOS_DARK,
    MACOS_LIGHT,
    ThemeColors,
    apply_fluent_theme,
    enable_windows_dpi_awareness,
    get_system_font,
    is_system_dark_theme,
    set_windows_titlebar_appearance,
)

def format_file_size(size_bytes: int) -> str:
    """Formats file size into a clean human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    num = float(size_bytes)
    for unit in ["KB", "MB", "GB"]:
        num /= 1024.0
        if num < 1024.0:
            return f"{num:.1f} {unit}"
    return f"{num:.1f} TB"

def format_detection_source(method: str, is_duplicate: bool) -> str:
    """Converts internal technical labels into clear, user-friendly terms."""
    if is_duplicate:
        return "Duplicate (Exact Match)"
    friendly = {
        "magic_bytes": "File Content Header",
        "text_heuristics": "Content Text Scan",
        "extension_fallback": "File Extension",
        "date_metadata": "Timeline Metadata",
    }
    return friendly.get(method, method)

class ByteSiftApp:
    def __init__(self, root: tk.Tk, initial_folder: Optional[str] = None, force_macos: bool = False):
        self.root = root
        self.force_macos = force_macos
        title_suffix = " (macOS Simulation)" if force_macos else ""
        self.root.title(f"ByteSift - Offline Content-Aware File Organizer{title_suffix}")
        self.root.geometry("960x680")
        self.root.minsize(760, 520)

        # High-DPI configuration for crisp Windows rendering
        enable_windows_dpi_awareness()

        # Register Windows AppUserModelID for independent taskbar grouping
        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Pramuditha.ByteSift.App.1.0")
            except (AttributeError, OSError):
                pass

        # State Variables
        self.current_plan: List[PlanItem] = []
        self.selected_folder = tk.StringVar(value=initial_folder or "")
        self.strategy_var = tk.StringVar(value="smart")
        self.group_date_var = tk.BooleanVar(value=False)
        self.duplicates_var = tk.BooleanVar(value=True)
        self.recursive_var = tk.BooleanVar(value=False)
        self.theme_mode_var = tk.StringVar(value="System")
        self.current_theme: ThemeColors = DARK_THEME
        self._latest_update_info: Optional[UpdateInfo] = None

        # Pre-load initial theme icon (white icon in dark mode, black icon in light mode)
        self._apply_window_icon(is_system_dark_theme())

        # Build native menu bar and shortcuts (integrated into macOS system menu)
        self._build_menu_bar()
        self._setup_keyboard_shortcuts()

        # Build UI layout
        self._build_ui()

        # Determine and apply initial theme
        self._sync_theme()

        # Start periodic background listener for system theme changes (macOS/Windows)
        self._schedule_system_theme_check()

        # Non-blocking background check for newer releases
        self._start_background_update_check()

        if initial_folder:
            self.on_scan()

    def _apply_window_icon(self, is_dark: bool):
        """
        Applies theme-synchronized icons:
        - White icon in dark mode (icon_dark.png / icon_dark.ico).
        - Black icon in light mode (icon_light.png / icon_light.ico).
        """
        # Resolve assets directory across frozen executables and development environments
        candidates = []
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if getattr(sys, "frozen", False):
            if bundle_dir:
                candidates.extend([
                    Path(bundle_dir) / "bytesift" / "assets",
                    Path(bundle_dir) / "assets",
                ])
            exe_dir = Path(sys.executable).resolve().parent
            candidates.extend([
                exe_dir / "bytesift" / "assets",
                exe_dir / "_internal" / "bytesift" / "assets",
                exe_dir / "assets",
            ])
        candidates.append(Path(__file__).resolve().parent.parent / "assets")
        assets_dir = next((c for c in candidates if c.exists()), candidates[-1])

        suffix = "dark" if is_dark else "light"
        ico_path = assets_dir / f"icon_{suffix}.ico"
        png_path = assets_dir / f"icon_{suffix}.png"

        # Apply native Windows ICO to title bar and taskbar
        if ico_path.exists():
            try:
                self.root.iconbitmap(str(ico_path))
                self.root.iconbitmap(default=str(ico_path))
            except (tk.TclError, OSError):
                pass

        # Apply PhotoImage icon for window, dialogs, and UI header
        if png_path.exists():
            try:
                self._icon_img = tk.PhotoImage(file=str(png_path))
                self.root.iconphoto(True, self._icon_img)
                # Subsample 512x512 down to crisp ~28x28 for UI header
                self._header_icon = self._icon_img.subsample(18, 18)
                if hasattr(self, "logo_lbl"):
                    self.logo_lbl.configure(image=self._header_icon)
                    self.logo_lbl.image = self._header_icon
            except (tk.TclError, OSError):
                pass

    def _sync_theme(self):
        """Resolves theme mode setting and applies color scheme."""
        mode = self.theme_mode_var.get()
        if mode == "Dark":
            is_dark = True
        elif mode == "Light":
            is_dark = False
        else:  # "System"
            is_dark = is_system_dark_theme()

        if self.force_macos:
            self.current_theme = MACOS_DARK if is_dark else MACOS_LIGHT
        else:
            self.current_theme = DARK_THEME if is_dark else LIGHT_THEME
        apply_fluent_theme(self.root, self.current_theme)
        self._apply_window_icon(is_dark)
        self._update_widget_colors()

    def _schedule_system_theme_check(self):
        """Polls system theme every 2.5 seconds when in System mode."""
        if self.theme_mode_var.get() == "System":
            sys_dark = is_system_dark_theme()
            current_is_dark = (self.current_theme.name == "dark")
            if sys_dark != current_is_dark:
                self._sync_theme()
        self.root.after(2500, self._schedule_system_theme_check)

    def _update_widget_colors(self):
        """Applies dynamic theme colors to custom frames and treeview tags."""
        theme = self.current_theme

        # Treeview row styling
        self.tree.tag_configure("even", background=theme.table_bg, foreground=theme.text_primary)
        self.tree.tag_configure("odd", background=theme.table_alt_bg, foreground=theme.text_primary)
        self.tree.tag_configure("duplicate", background=theme.warning_bg, foreground=theme.warning_text)

        # Re-apply tag colors to any existing items in the table
        for idx, item in enumerate(self.tree.get_children()):
            values = self.tree.item(item, "values")
            if len(values) >= 4 and "Duplicate" in str(values[3]):
                self.tree.item(item, tags=("duplicate",))
            else:
                self.tree.item(item, tags=("odd" if idx % 2 == 1 else "even",))

        # Force title bar update
        set_windows_titlebar_appearance(self.root, theme.name == "dark")

    def _start_background_update_check(self):
        """Non-blocking background release check that fails silently if offline."""
        def worker():
            try:
                info = check_for_updates(current_version=__version__, timeout=3.5)
                if info and info.has_update:
                    self.root.after(0, lambda: self._notify_update_available(info))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _notify_update_available(self, info: UpdateInfo):
        """Reveals the update button in the status bar when an update is found."""
        self._latest_update_info = info
        if hasattr(self, "update_btn"):
            self.update_btn.configure(text=f"🚀 v{info.latest_version} Available")
            self.update_btn.pack(side=tk.RIGHT, padx=(8, 0))

    def on_show_update_dialog(self):
        """Presents release notes and direct update link dialog."""
        info = self._latest_update_info
        if not info:
            self.on_check_updates_manual()
            return
        self._prompt_update_dialog(info)

    def on_check_updates_manual(self):
        """Interactive update check triggered from the Help menu."""
        self.status_var.set("Checking GitHub Releases for updates...")
        def worker():
            info = check_for_updates(current_version=__version__, timeout=5.0)
            def done():
                self.status_var.set("Ready.")
                if not info:
                    messagebox.showwarning(
                        "Update Check",
                        "Unable to connect to GitHub.\n\n"
                        "Please check your internet connection or visit the releases page:\n"
                        "https://github.com/PramudithaN/bytesift/releases"
                    )
                elif info.has_update:
                    self._notify_update_available(info)
                    self._prompt_update_dialog(info)
                else:
                    messagebox.showinfo(
                        "ByteSift Up to Date",
                        f"You're using the latest version of ByteSift (v{__version__}).\n\n"
                        "No updates are currently available."
                    )
            self.root.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def _prompt_update_dialog(self, info: UpdateInfo):
        notes_preview = ""
        if info.release_notes:
            first_lines = "\n".join(info.release_notes.strip().splitlines()[:6])
            notes_preview = f"\n\nWhat's New:\n{first_lines}"
            if len(info.release_notes.splitlines()) > 6:
                notes_preview += "\n..."

        resp = messagebox.askyesno(
            "ByteSift Update Available",
            f"A newer version of ByteSift is available!\n\n"
            f"Current version: v{info.current_version}\n"
            f"Latest version: v{info.latest_version} ({info.release_name})"
            f"{notes_preview}\n\n"
            f"Would you like to open the download page in your browser?"
        )
        if resp:
            webbrowser.open(info.download_url or info.html_url)

    def _build_menu_bar(self):
        """Builds native top menu bar (integrated into macOS system menu on Mac)."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        mod = "⌘" if sys.platform == "darwin" else "Ctrl"

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Folder...", accelerator=f"{mod}+O", command=self.on_browse)
        file_menu.add_command(label="Refresh Preview", accelerator=f"{mod}+R", command=self.on_scan)
        open_lbl = "Reveal in Finder" if sys.platform == "darwin" else "Open in File Explorer"
        file_menu.add_command(label=open_lbl, command=self.on_open_in_explorer)
        file_menu.add_separator()
        file_menu.add_command(label="Organize Files", accelerator=f"{mod}+Enter", command=self.on_organize)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo Organization", accelerator=f"{mod}+Z", command=self.on_undo)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_radiobutton(label="System Theme", variable=self.theme_mode_var, value="System", command=self._sync_theme)
        view_menu.add_radiobutton(label="Dark Mode", variable=self.theme_mode_var, value="Dark", command=self._sync_theme)
        view_menu.add_radiobutton(label="Light Mode", variable=self.theme_mode_var, value="Light", command=self._sync_theme)
        menubar.add_cascade(label="View", menu=view_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Check for Updates...", command=self.on_check_updates_manual)
        help_menu.add_command(label="Visit Website...", command=lambda: webbrowser.open("https://pramudithan.github.io/bytesift/"))
        help_menu.add_separator()
        help_menu.add_command(label="About ByteSift", command=self.on_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def _setup_keyboard_shortcuts(self):
        """Binds standard macOS (Command) and Windows/Linux (Control) shortcuts."""
        mod = "Command" if sys.platform == "darwin" else "Control"
        self.root.bind(f"<{mod}-o>", lambda e: self.on_browse())
        self.root.bind(f"<{mod}-r>", lambda e: self.on_scan())
        self.root.bind(f"<{mod}-z>", lambda e: self.on_undo())
        self.root.bind(f"<{mod}-Return>", lambda e: self.on_organize())

    def on_about(self):
        """Displays About ByteSift dialog."""
        update_text = ""
        if self._latest_update_info and self._latest_update_info.has_update:
            update_text = f"\n\n🚀 Update v{self._latest_update_info.latest_version} is available!"
        messagebox.showinfo(
            "About ByteSift",
            f"ByteSift v{__version__}{update_text}\n\n"
            "Lightweight, 100% offline file content examiner and organizer.\n"
            "Designed for macOS, Windows, and Linux without external dependencies.\n\n"
            "Official Website & Docs:\nhttps://pramudithan.github.io/bytesift/"
        )

    def _build_ui(self):
        # 1. Top Navigation & Header Bar
        header_frame = ttk.Frame(self.root, padding="20 16 20 8")
        header_frame.pack(fill=tk.X)

        header_left = ttk.Frame(header_frame)
        header_left.pack(side=tk.LEFT, fill=tk.Y)

        self.logo_lbl = ttk.Label(header_left, style="TLabel")
        if hasattr(self, "_header_icon"):
            self.logo_lbl.configure(image=self._header_icon)
        self.logo_lbl.pack(side=tk.LEFT, padx=(0, 10))

        title_lbl = ttk.Label(
            header_left,
            text="ByteSift",
            style="Title.TLabel"
        )
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = ttk.Label(
            header_left,
            text="  Offline Content-Aware File Organizer",
            style="Subtitle.TLabel"
        )
        subtitle_lbl.pack(side=tk.LEFT, padx=(6, 0), pady=(4, 0))

        # Top Right: Theme Mode Switcher
        header_right = ttk.Frame(header_frame)
        header_right.pack(side=tk.RIGHT)

        ttk.Label(header_right, text="Theme:", style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(0, 6))
        theme_combo = ttk.Combobox(
            header_right,
            textvariable=self.theme_mode_var,
            values=["System", "Dark", "Light"],
            state="readonly",
            width=8
        )
        theme_combo.pack(side=tk.LEFT)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self._sync_theme())

        # Main Scrollable / Padded Container
        container = ttk.Frame(self.root, padding="20 4 20 12")
        container.pack(fill=tk.BOTH, expand=True)

        # 2. Card: Target Folder Picker
        self.card_dir = ttk.Frame(container, style="CardContent.TFrame", padding="14")
        self.card_dir.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.card_dir, text="Target Directory", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 6))

        dir_input_row = ttk.Frame(self.card_dir, style="CardContent.TFrame")
        dir_input_row.pack(fill=tk.X)

        self.dir_entry = ttk.Entry(dir_input_row, textvariable=self.selected_folder, font=get_system_font(9))
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.dir_entry.bind("<Return>", lambda e: self.on_scan())

        browse_btn = ttk.Button(dir_input_row, text="Browse Folder", command=self.on_browse)
        browse_btn.pack(side=tk.LEFT, padx=(0, 6))

        open_btn_text = "Reveal in Finder" if sys.platform == "darwin" else "Open in File Explorer"
        open_folder_btn = ttk.Button(dir_input_row, text=open_btn_text, command=self.on_open_in_explorer)
        open_folder_btn.pack(side=tk.LEFT)

        # 3. Card: Rules & Strategy Controls
        self.card_opts = ttk.Frame(container, style="CardContent.TFrame", padding="14")
        self.card_opts.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.card_opts, text="Organization Strategy & Options", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 8))

        opts_row = ttk.Frame(self.card_opts, style="CardContent.TFrame")
        opts_row.pack(fill=tk.X)

        ttk.Label(opts_row, text="Mode:", style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(0, 6))

        strategy_combo = ttk.Combobox(
            opts_row,
            textvariable=self.strategy_var,
            values=["smart", "date", "type"],
            state="readonly",
            width=10
        )
        strategy_combo.pack(side=tk.LEFT, padx=(0, 16))

        date_chk = ttk.Checkbutton(opts_row, text="Group Media by Month", variable=self.group_date_var)
        date_chk.pack(side=tk.LEFT, padx=(0, 16))

        dup_chk = ttk.Checkbutton(opts_row, text="Detect Duplicate Files", variable=self.duplicates_var)
        dup_chk.pack(side=tk.LEFT, padx=(0, 16))

        rec_chk = ttk.Checkbutton(opts_row, text="Scan Subfolders Recursively", variable=self.recursive_var)
        rec_chk.pack(side=tk.LEFT)

        # 4. Action Command Bar
        action_bar = ttk.Frame(container)
        action_bar.pack(fill=tk.X, pady=(0, 10))

        self.scan_btn = ttk.Button(
            action_bar,
            text="Inspect & Preview",
            style="Accent.TButton",
            command=self.on_scan
        )
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.organize_btn = ttk.Button(
            action_bar,
            text="Organize Files",
            style="Success.TButton",
            state=tk.DISABLED,
            command=self.on_organize
        )
        self.organize_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.undo_btn = ttk.Button(
            action_bar,
            text="Undo Last Session",
            command=self.on_undo
        )
        self.undo_btn.pack(side=tk.LEFT)

        # 5. Card: Preview Table
        self.card_table = ttk.Frame(container, style="CardContent.TFrame", padding="2")
        self.card_table.pack(fill=tk.BOTH, expand=True)

        columns = ("file", "size", "category", "method")
        self.tree = ttk.Treeview(
            self.card_table,
            columns=columns,
            show="headings",
            selectmode="extended"
        )
        self.tree.heading("file", text="Filename", anchor=tk.W)
        self.tree.heading("size", text="Size", anchor=tk.E)
        self.tree.heading("category", text="Target Folder", anchor=tk.W)
        self.tree.heading("method", text="Detected By", anchor=tk.W)

        self.tree.column("file", width=340, anchor=tk.W)
        self.tree.column("size", width=95, anchor=tk.E)
        self.tree.column("category", width=230, anchor=tk.W)
        self.tree.column("method", width=190, anchor=tk.W)

        scroll_y = ttk.Scrollbar(self.card_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 6. Modern Status Bar
        self.status_frame = ttk.Frame(self.root, style="Status.TFrame", padding="16 8")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar(value="Ready. Select a target directory to begin.")
        status_lbl = ttk.Label(self.status_frame, textvariable=self.status_var, style="Status.TLabel")
        status_lbl.pack(side=tk.LEFT)

        # Hidden by default; displayed when an update is available
        self.update_btn = ttk.Button(
            self.status_frame,
            text="🚀 Update Available",
            command=self.on_show_update_dialog
        )

    def on_browse(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.selected_folder.set(folder)
            self.on_scan()

    def on_open_in_explorer(self):
        folder_str = self.selected_folder.get().strip()
        if not folder_str or not Path(folder_str).is_dir():
            messagebox.showwarning("Notice", "Please select a valid folder first.")
            return
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(Path(folder_str).resolve())])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(Path(folder_str).resolve())])
        else:
            subprocess.Popen(["xdg-open", str(Path(folder_str).resolve())])

    def on_scan(self):
        folder_str = self.selected_folder.get().strip()
        if not folder_str:
            messagebox.showwarning("Notice", "Please select a target folder.")
            return

        folder = Path(folder_str)
        if not folder.is_dir():
            messagebox.showerror("Error", f"Folder does not exist:\n{folder_str}")
            return

        self.status_var.set("Inspecting directory contents...")
        self.scan_btn.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())

        def run_scan():
            config = OrganizerConfig(
                strategy=self.strategy_var.get(),
                group_by_date=self.group_date_var.get(),
                detect_duplicates=self.duplicates_var.get(),
                recursive=self.recursive_var.get()
            )
            organizer = Organizer(config)
            try:
                plan = organizer.generate_plan(folder)
            except PermissionError:
                def alert_permission():
                    self.scan_btn.config(state=tk.NORMAL)
                    self.status_var.set("Access denied by system security.")
                    if sys.platform == "darwin":
                        messagebox.showwarning(
                            "macOS Permission Required",
                            f"ByteSift was denied access to '{folder.name}'.\n\n"
                            "macOS requires explicit permission for user folders (Documents, Downloads, Desktop).\n\n"
                            "To grant access:\n"
                            "1. Open Apple Menu > System Settings.\n"
                            "2. Navigate to 'Privacy & Security' > 'Files and Folders'.\n"
                            "3. Enable access for Terminal / Python."
                        )
                    else:
                        messagebox.showwarning("Permission Denied", f"Access denied to '{folder}'.")
                self.root.after(0, alert_permission)
                return

            def update_ui():
                self.current_plan = plan
                for idx, item in enumerate(plan):
                    try:
                        sz = item.source.stat().st_size
                        size_str = format_file_size(sz)
                    except OSError:
                        size_str = "-"

                    method_str = format_detection_source(item.method, item.is_duplicate)
                    tag = "duplicate" if item.is_duplicate else ("odd" if idx % 2 == 1 else "even")

                    self.tree.insert("", tk.END, values=(
                        item.source.name,
                        size_str,
                        item.target_category,
                        method_str
                    ), tags=(tag,))

                count = len(plan)
                self.status_var.set(f"Scan complete. {count} item(s) ready to organize.")
                self.scan_btn.config(state=tk.NORMAL)
                if count > 0:
                    self.organize_btn.config(state=tk.NORMAL)
                else:
                    self.organize_btn.config(state=tk.DISABLED)

            self.root.after(0, update_ui)

        threading.Thread(target=run_scan, daemon=True).start()

    def on_organize(self):
        if not self.current_plan:
            messagebox.showinfo("Information", "No files scheduled to organize.")
            return

        count = len(self.current_plan)
        confirm = messagebox.askyesno(
            "Confirm Organization",
            f"Organize {count} file(s) into categorized subfolders?\n\nThis action can be rolled back at any time."
        )
        if not confirm:
            return

        folder = Path(self.selected_folder.get().strip())
        config = OrganizerConfig(
            strategy=self.strategy_var.get(),
            group_by_date=self.group_date_var.get(),
            detect_duplicates=self.duplicates_var.get(),
            recursive=self.recursive_var.get()
        )
        organizer = Organizer(config)

        self.status_var.set("Relocating files...")
        self.organize_btn.config(state=tk.DISABLED)

        def run_move():
            moved = organizer.execute_plan(folder, self.current_plan)
            def done():
                messagebox.showinfo("Complete", f"Successfully organized {moved} file(s).")
                self.tree.delete(*self.tree.get_children())
                self.current_plan = []
                self.status_var.set(f"Organization finished. {moved} file(s) moved.")
            self.root.after(0, done)

        threading.Thread(target=run_move, daemon=True).start()

    def on_undo(self):
        folder_str = self.selected_folder.get().strip()
        if not folder_str:
            messagebox.showwarning("Notice", "Please select a target folder.")
            return

        folder = Path(folder_str)
        if not folder.is_dir():
            messagebox.showerror("Error", f"Folder does not exist:\n{folder_str}")
            return

        confirm = messagebox.askyesno(
            "Confirm Rollback",
            f"Undo the previous organization session in:\n{folder}?"
        )
        if not confirm:
            return

        mgr = TransactionManager(folder)
        reverted, errors = mgr.undo_last_session()

        if errors:
            msg = "\n".join(errors[:4])
            messagebox.showwarning("Notice", f"Rollback completed with warnings:\n{msg}")

        if reverted > 0:
            messagebox.showinfo("Rollback Complete", f"Successfully restored {reverted} file(s) to original paths.")
            self.on_scan()
        else:
            messagebox.showinfo("Notice", "No previous session records found to undo.")

def launch_gui(initial_folder: Optional[str] = None, force_macos: bool = False):
    root = tk.Tk()
    ByteSiftApp(root, initial_folder, force_macos=force_macos)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
