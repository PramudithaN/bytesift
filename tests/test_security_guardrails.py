"""
Unit and integration tests for ByteSift Security Guardrails.
Verifies system directory protection, symlink isolation, path traversal defense,
Windows reserved device rejection, and crash-safe transaction logging.
"""

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from bytesift.core.organizer import Organizer, OrganizerConfig, PlanItem
from bytesift.core.security import (
    is_critical_system_path,
    is_safe_target_directory,
    is_safe_file_to_process,
    WIN32_RESERVED_NAMES
)
from bytesift.core.transaction import TransactionManager, FileMoveRecord
from bytesift.inspectors.magic_bytes import inspect_magic_bytes
from bytesift.inspectors.hasher import calculate_file_hash, find_duplicate_groups

class TestSecurityGuardrails(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="bytesift_sec_test_"))

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_critical_system_paths_detected(self):
        # Filesystem roots must be critical
        root_path = Path("C:\\").resolve() if sys.platform == "win32" else Path("/").resolve()
        self.assertTrue(is_critical_system_path(root_path))

        # Windows system dirs
        if sys.platform == "win32":
            win_dir = Path(os.environ.get("SystemRoot", r"C:\Windows")).resolve()
            self.assertTrue(is_critical_system_path(win_dir))
            sys32 = win_dir / "System32"
            self.assertTrue(is_critical_system_path(sys32))
        else:
            self.assertTrue(is_critical_system_path(Path("/etc").resolve()))
            self.assertTrue(is_critical_system_path(Path("/bin").resolve()))

        # Normal temporary or user folder must not be critical
        self.assertFalse(is_critical_system_path(self.test_dir.resolve()))

    def test_refuse_organizing_system_directory(self):
        root_path = Path("C:\\").resolve() if sys.platform == "win32" else Path("/").resolve()
        safe, err = is_safe_target_directory(root_path)
        self.assertFalse(safe)
        self.assertIn("Access Denied", err)

        organizer = Organizer()
        with self.assertRaises(PermissionError):
            organizer.generate_plan(root_path)

        with self.assertRaises(PermissionError):
            organizer.execute_plan(root_path, [])

    def test_symlinks_are_never_scanned_or_moved(self):
        regular_file = self.test_dir / "regular.txt"
        regular_file.write_text("Regular content", encoding="utf-8")

        symlink_file = self.test_dir / "link_to_regular.txt"
        try:
            os.symlink(regular_file, symlink_file)
        except (OSError, NotImplementedError):
            # Non-elevated Windows might disallow creating symlinks
            return

        # is_safe_file_to_process must reject symlink
        self.assertTrue(is_safe_file_to_process(regular_file, self.test_dir))
        self.assertFalse(is_safe_file_to_process(symlink_file, self.test_dir))

        # scan_files must only collect regular file
        organizer = Organizer(OrganizerConfig(recursive=False))
        scanned = organizer.scan_files(self.test_dir)
        self.assertIn(regular_file, scanned)
        self.assertNotIn(symlink_file, scanned)

        # Hasher and magic bytes must refuse symlink
        self.assertEqual(calculate_file_hash(symlink_file), "")
        self.assertIsNone(inspect_magic_bytes(symlink_file))

    def test_poisoned_history_journal_path_traversal_blocked(self):
        # Create dummy source file inside test_dir
        src_file = self.test_dir / "categorized.txt"
        src_file.write_text("Hello", encoding="utf-8")

        # Create poisoned history pointing outside test_dir (e.g. to C:\Windows or /etc)
        poisoned_dest = Path("C:\\Windows\\system_file.dll") if sys.platform == "win32" else Path("/etc/shadow")
        history_path = self.test_dir / ".bytesift_history.json"
        poisoned_data = [
            {
                "timestamp": "2026-11-10T12:00:00",
                "base_folder": str(self.test_dir.resolve()),
                "moves": [
                    {
                        "original_path": str(poisoned_dest),
                        "target_path": str(src_file.resolve()),
                    }
                ]
            }
        ]
        history_path.write_text(json.dumps(poisoned_data), encoding="utf-8")

        mgr = TransactionManager(self.test_dir)
        reverted, errors = mgr.undo_last_session()

        # Rollback must be blocked
        self.assertEqual(reverted, 0)
        self.assertTrue(any("Blocked" in e or "Security Alert" in e for e in errors))
        # Ensure source file was NOT moved
        self.assertTrue(src_file.exists())

    def test_windows_reserved_device_names_rejected(self):
        if sys.platform != "win32":
            return

        # Test reserved name check
        for name in ("con.txt", "prn.pdf", "aux.log", "nul", "com1.txt", "lpt2.dat"):
            f = self.test_dir / name
            self.assertFalse(is_safe_file_to_process(f, self.test_dir))

    def test_crash_safe_wal_transactions(self):
        organizer = Organizer()
        file1 = self.test_dir / "f1.txt"
        file2 = self.test_dir / "f2.txt"
        file1.write_text("file 1 content", encoding="utf-8")
        file2.write_text("file 2 content", encoding="utf-8")

        plan = organizer.generate_plan(self.test_dir)
        self.assertEqual(len(plan), 2)

        # Execute
        moved = organizer.execute_plan(self.test_dir, plan)
        self.assertEqual(moved, 2)

        # Verify journal exists and has 2 recorded moves
        mgr = TransactionManager(self.test_dir)
        sessions = mgr.load_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(len(sessions[0]["moves"]), 2)

        # Verify rollback restores files
        reverted, errors = mgr.undo_last_session()
        self.assertEqual(reverted, 2)
        self.assertEqual(errors, [])
        self.assertTrue(file1.exists())
        self.assertTrue(file2.exists())

if __name__ == "__main__":
    unittest.main()
