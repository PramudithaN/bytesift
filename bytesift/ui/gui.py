"""
ByteSift Desktop GUI
Ultra-lightweight, zero-dependency native interface using Tkinter.
"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Optional
from bytesift.core.organizer import Organizer, OrganizerConfig, PlanItem
from bytesift.core.transaction import TransactionManager

class ByteSiftApp:
    def __init__(self, root: tk.Tk, initial_folder: Optional[str] = None):
        self.root = root
        self.root.title("ByteSift - Content-Aware Offline File Organizer")
        self.root.geometry("880x620")
        self.root.minsize(700, 480)

        self.current_plan: List[PlanItem] = []
        self.selected_folder = tk.StringVar(value=initial_folder or "")
        self.strategy_var = tk.StringVar(value="smart")
        self.group_date_var = tk.BooleanVar(value=False)
        self.duplicates_var = tk.BooleanVar(value=True)
        self.recursive_var = tk.BooleanVar(value=False)

        self._apply_styles()
        self._build_ui()

        if initial_folder:
            self.on_scan()

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure fonts and treeview colors
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TButton", font=("Segoe UI", 9), padding=5)
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), foreground="#0055aa")

    def _build_ui(self):
        # 1. Top Header Frame
        header_frame = ttk.Frame(self.root, padding="15 10 15 5")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text="ByteSift",
            font=("Segoe UI", 16, "bold"),
            foreground="#1a5fb4"
        )
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = ttk.Label(
            header_frame,
            text="— 100% Offline Content Inspector & File Organizer",
            font=("Segoe UI", 10),
            foreground="#555555"
        )
        subtitle_lbl.pack(side=tk.LEFT, padx=10, pady=(4, 0))

        # 2. Directory Selector Frame
        dir_frame = ttk.LabelFrame(self.root, text=" Target Directory ", padding="10")
        dir_frame.pack(fill=tk.X, padx=15, pady=5)

        dir_entry = ttk.Entry(dir_frame, textvariable=self.selected_folder, font=("Segoe UI", 9))
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ttk.Button(dir_frame, text="Browse...", command=self.on_browse)
        browse_btn.pack(side=tk.RIGHT)

        # 3. Settings & Options Frame
        opts_frame = ttk.Frame(self.root, padding="15 5")
        opts_frame.pack(fill=tk.X)

        ttk.Label(opts_frame, text="Strategy:").pack(side=tk.LEFT, padx=(0, 5))
        strategy_combo = ttk.Combobox(
            opts_frame,
            textvariable=self.strategy_var,
            values=["smart", "date", "type"],
            state="readonly",
            width=10
        )
        strategy_combo.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Checkbutton(opts_frame, text="Detect Duplicates", variable=self.duplicates_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(opts_frame, text="Group Media by Date", variable=self.group_date_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(opts_frame, text="Recursive Scan", variable=self.recursive_var).pack(side=tk.LEFT, padx=10)

        # 4. Action Buttons Frame
        btn_frame = ttk.Frame(self.root, padding="15 5")
        btn_frame.pack(fill=tk.X)

        self.scan_btn = ttk.Button(btn_frame, text="🔍 Preview Scan", command=self.on_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.organize_btn = ttk.Button(
            btn_frame,
            text="⚡ Organize Files",
            style="Accent.TButton",
            command=self.on_organize,
            state=tk.DISABLED
        )
        self.organize_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.undo_btn = ttk.Button(btn_frame, text="↩️ Undo Last Run", command=self.on_undo)
        self.undo_btn.pack(side=tk.LEFT)

        # 5. Treeview (Plan Table)
        table_frame = ttk.Frame(self.root, padding="15 5")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("file", "category", "method", "duplicate")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("file", text="Original File Name")
        self.tree.heading("category", text="Destination Category")
        self.tree.heading("method", text="Inspection Method")
        self.tree.heading("duplicate", text="Duplicate?")

        self.tree.column("file", width=280)
        self.tree.column("category", width=220)
        self.tree.column("method", width=140)
        self.tree.column("duplicate", width=90, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 6. Status Bar
        self.status_var = tk.StringVar(value="Select a folder to begin.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def on_browse(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.selected_folder.set(folder)
            self.on_scan()

    def on_scan(self):
        folder_str = self.selected_folder.get().strip()
        if not folder_str:
            messagebox.showwarning("Warning", "Please select a target folder first.")
            return

        folder = Path(folder_str)
        if not folder.is_dir():
            messagebox.showerror("Error", f"Folder does not exist:\n{folder_str}")
            return

        self.status_var.set("Scanning contents...")
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
            plan = organizer.generate_plan(folder)

            def update_ui():
                self.current_plan = plan
                for item in plan:
                    dup_text = "YES" if item.is_duplicate else "-"
                    self.tree.insert("", tk.END, values=(
                        item.source.name,
                        item.target_category,
                        item.method,
                        dup_text
                    ))

                count = len(plan)
                self.status_var.set(f"Scan complete. {count} file(s) ready to be organized.")
                self.scan_btn.config(state=tk.NORMAL)
                if count > 0:
                    self.organize_btn.config(state=tk.NORMAL)
                else:
                    self.organize_btn.config(state=tk.DISABLED)

            self.root.after(0, update_ui)

        threading.Thread(target=run_scan, daemon=True).start()

    def on_organize(self):
        if not self.current_plan:
            messagebox.showinfo("Info", "No files to organize.")
            return

        count = len(self.current_plan)
        confirm = messagebox.askyesno(
            "Confirm Organization",
            f"Are you sure you want to organize {count} file(s)?\n\nYou can undo this action at any time."
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

        self.status_var.set("Organizing files...")
        self.organize_btn.config(state=tk.DISABLED)

        def run_move():
            moved = organizer.execute_plan(folder, self.current_plan)
            def done():
                messagebox.showinfo("Success", f"Successfully organized {moved} file(s)!")
                self.tree.delete(*self.tree.get_children())
                self.current_plan = []
                self.status_var.set(f"Completed. {moved} file(s) moved.")
            self.root.after(0, done)

        threading.Thread(target=run_move, daemon=True).start()

    def on_undo(self):
        folder_str = self.selected_folder.get().strip()
        if not folder_str:
            messagebox.showwarning("Warning", "Please select a target folder.")
            return

        folder = Path(folder_str)
        if not folder.is_dir():
            messagebox.showerror("Error", f"Invalid folder:\n{folder_str}")
            return

        confirm = messagebox.askyesno(
            "Confirm Rollback",
            f"Do you want to undo the last organization operation in:\n{folder}?"
        )
        if not confirm:
            return

        mgr = TransactionManager(folder)
        reverted, errors = mgr.undo_last_session()

        if errors:
            msg = "\n".join(errors[:5])
            messagebox.showwarning("Undo Warning", f"Encountered issues:\n{msg}")

        if reverted > 0:
            messagebox.showinfo("Rollback Complete", f"Successfully restored {reverted} file(s)!")
            self.on_scan()
        else:
            messagebox.showinfo("Undo", "No previous actions found to undo.")

def launch_gui(initial_folder: Optional[str] = None):
    root = tk.Tk()
    app = ByteSiftApp(root, initial_folder)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
