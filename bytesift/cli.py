"""
ByteSift Command Line Interface
Fast, lightweight, offline file organizer CLI.
"""

import argparse
import sys
from pathlib import Path
from typing import List
from bytesift import __version__
from bytesift.core.organizer import Organizer, OrganizerConfig, PlanItem
from bytesift.core.transaction import TransactionManager
from bytesift.core.updater import check_for_updates

def print_banner():
    banner = r"""
  ____        _       ____  _  __ _   
 | __ ) _   _| |_ ___/ ___|(_)/ _| |_ 
 |  _ \| | | | __/ _ \___ \| | |_| __|
 | |_) | |_| | ||  __/___) | |  _| |_ 
 |____/ \__, |\__\___|____/|_|_|  \__|
        |___/    Offline Content Organizer
    """
    print(banner)

def display_plan(plan: List[PlanItem], base_folder: Path):
    if not plan:
        print("\nAll files are already organized or folder is empty.")
        return

    print(f"\nFound {len(plan)} file(s) to organize in '{base_folder}':\n")
    print(f"{'FILE':<32} {'CATEGORY':<28} {'METHOD':<18}")
    print("-" * 80)

    for item in plan:
        fname = item.source.name
        if len(fname) > 30:
            fname = fname[:27] + "..."
        cat = item.target_category
        if len(cat) > 26:
            cat = cat[:23] + "..."
        method = item.method
        if item.is_duplicate:
            method += " [DUP]"
        print(f"{fname:<32} {cat:<28} {method:<18}")

    print("-" * 80)
    print(f"Total actions to execute: {len(plan)}")

def cmd_scan(args):
    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"Error: Directory '{folder}' does not exist.")
        sys.exit(1)

    config = OrganizerConfig(
        strategy=args.strategy,
        group_by_date=args.group_by_date,
        detect_duplicates=not args.no_duplicates,
        recursive=args.recursive
    )
    organizer = Organizer(config)
    plan = organizer.generate_plan(folder)
    display_plan(plan, folder)
    print("\nRun 'bytesift organize' to apply these changes.")

def cmd_organize(args):
    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"Error: Directory '{folder}' does not exist.")
        sys.exit(1)

    config = OrganizerConfig(
        strategy=args.strategy,
        group_by_date=args.group_by_date,
        detect_duplicates=not args.no_duplicates,
        recursive=args.recursive
    )
    organizer = Organizer(config)
    plan = organizer.generate_plan(folder)
    display_plan(plan, folder)

    if not plan:
        return

    if args.dry_run:
        print("\n[DRY RUN] No files were moved.")
        return

    if not args.yes:
        confirm = input("\nProceed with moving these files? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Aborted by user.")
            return

    print("\nMoving files...")
    moved = organizer.execute_plan(folder, plan)
    print(f"Successfully organized {moved} file(s).")
    print("To revert anytime, run: bytesift undo \"{folder}\"")

def cmd_undo(args):
    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"Error: Directory '{folder}' does not exist.")
        sys.exit(1)

    transaction_mgr = TransactionManager(folder)
    if not transaction_mgr.history_file.exists():
        print(f"No previous organization session found in '{folder}'.")
        return

    reverted, errors = transaction_mgr.undo_last_session()
    if errors:
        print(f"Encountered {len(errors)} error(s) during rollback:")
        for err in errors:
            print(f"  - {err}")

    if reverted > 0:
        print(f"Successfully rolled back {reverted} file(s) to original locations.")
    else:
        print("No files were restored.")

def cmd_gui(args):
    try:
        from bytesift.ui.gui import launch_gui
        force_mac = getattr(args, "macos", False)
        launch_gui(args.folder if hasattr(args, "folder") and args.folder else None, force_macos=force_mac)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)

def cmd_check_update(args):
    print(f"ByteSift v{__version__} - Checking for updates...")
    info = check_for_updates(current_version=__version__)
    if not info:
        print("Could not reach GitHub Releases. Please check your internet connection.")
        print("Manual download: https://github.com/PramudithaN/bytesift/releases/latest")
        return

    if info.has_update:
        print(f"\n[UPDATE] A new version is available: v{info.latest_version} (Current: v{info.current_version})")
        if info.release_name:
            print(f"Title: {info.release_name}")
        if info.release_notes:
            print("\nRelease Notes:")
            preview = info.release_notes[:400] + ("..." if len(info.release_notes) > 400 else "")
            print(preview)
        print(f"\nDownload: {info.download_url or info.html_url}")
    else:
        print(f"ByteSift is up to date (v{__version__}).")

def main():
    parser = argparse.ArgumentParser(
        prog="bytesift",
        description="Lightweight, 100% offline file content examiner and organizer.",
        epilog="Website & Documentation: https://pramudithan.github.io/bytesift/"
    )
    parser.add_argument("-v", "--version", action="version", version=f"ByteSift v{__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Common options helper
    def add_common_options(p):
        p.add_argument("folder", help="Target folder path to organize")
        p.add_argument("--strategy", choices=["smart", "date", "type"], default="smart",
                       help="Organization strategy: 'smart' (content heuristics), 'date' (timeline), 'type' (formats)")
        p.add_argument("--group-by-date", action="store_true", help="Group media into subfolders by year/month")
        p.add_argument("--no-duplicates", action="store_true", help="Disable duplicate file detection")
        p.add_argument("-r", "--recursive", action="store_true", help="Scan nested subfolders recursively")

    # Scan command
    p_scan = subparsers.add_parser("scan", help="Scan and preview organization plan without moving files")
    add_common_options(p_scan)
    p_scan.set_defaults(func=cmd_scan)

    # Organize command
    p_org = subparsers.add_parser("organize", help="Scan and organize files in folder")
    add_common_options(p_org)
    p_org.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    p_org.add_argument("--dry-run", action="store_true", help="Preview only, do not move files")
    p_org.set_defaults(func=cmd_organize)

    # Undo command
    p_undo = subparsers.add_parser("undo", help="Roll back the previous organization in the specified folder")
    p_undo.add_argument("folder", help="Target folder path containing history journal")
    p_undo.set_defaults(func=cmd_undo)

    # GUI command
    p_gui = subparsers.add_parser("gui", help="Launch the lightweight desktop GUI")
    p_gui.add_argument("folder", nargs="?", default=None, help="Optional initial directory to open")
    p_gui.add_argument("--macos", "--mac", action="store_true", help="Launch GUI with macOS Aqua theme and styling")
    p_gui.set_defaults(func=cmd_gui)

    # Check for updates command
    p_update = subparsers.add_parser("check-update", help="Check if a newer version of ByteSift is available on GitHub")
    p_update.set_defaults(func=cmd_check_update)

    if len(sys.argv) == 1:
        # Default to desktop GUI when launched without subcommands (e.g. double-clicked executable)
        try:
            from bytesift.ui.gui import launch_gui
            launch_gui()
            sys.exit(0)
        except Exception:
            print_banner()
            parser.print_help()
            sys.exit(0)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
