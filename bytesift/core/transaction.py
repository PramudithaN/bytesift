"""
ByteSift Transaction & History Log
Maintains a local journal of moved files for one-click rollback (Undo).
Includes strict cryptographic/path boundaries to prevent arbitrary file moves.
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import shutil
from typing import List, Optional, Tuple

from bytesift.core.security import is_critical_system_path

logger = logging.getLogger(__name__)
JOURNAL_FILENAME = ".bytesift_history.json"

@dataclass
class FileMoveRecord:
    original_path: str
    target_path: str

@dataclass
class SessionRecord:
    timestamp: str
    base_folder: str
    moves: List[dict]

class TransactionManager:
    def __init__(self, base_folder: Path):
        self.base_folder = base_folder
        self.journal_path = self.base_folder / JOURNAL_FILENAME

    @property
    def history_file(self) -> Path:
        """Alias for journal_path."""
        return self.journal_path

    def start_session(self) -> None:
        """Starts a new empty organization session in the journal."""
        sessions = self.load_sessions()
        session = SessionRecord(
            timestamp=datetime.now().isoformat(),
            base_folder=str(self.base_folder.resolve()),
            moves=[]
        )
        sessions.append(asdict(session))
        self._atomic_write_sessions(sessions)

    def record_move(self, move: FileMoveRecord) -> None:
        """Appends a single move to the current active session atomically (WAL)."""
        sessions = self.load_sessions()
        if not sessions:
            self.start_session()
            sessions = self.load_sessions()

        sessions[-1]["moves"].append(asdict(move))
        self._atomic_write_sessions(sessions)

    def save_session(self, moves: List[FileMoveRecord]) -> None:
        """Appends a complete organization session to the journal atomically."""
        if not moves:
            return

        sessions = self.load_sessions()
        session = SessionRecord(
            timestamp=datetime.now().isoformat(),
            base_folder=str(self.base_folder.resolve()),
            moves=[asdict(m) for m in moves]
        )
        sessions.append(asdict(session))
        self._atomic_write_sessions(sessions)

    def _atomic_write_sessions(self, sessions: List[dict]) -> None:
        """Writes journal sessions atomically using fsync and replace to prevent corruption."""
        tmp_path = self.base_folder / f"{JOURNAL_FILENAME}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.journal_path)
        except OSError as e:
            logger.warning("Failed to write undo journal: %s", e)
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def load_sessions(self) -> List[dict]:
        """Loads previous sessions from the journal file."""
        if not self.journal_path.exists():
            return []
        try:
            with open(self.journal_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def undo_last_session(self) -> Tuple[int, List[str]]:
        """
        Reverts the most recent session's file moves with path confinement security.
        Guarantees no file is moved outside base_folder or into protected system areas.
        Returns (num_reverted, list_of_errors).
        """
        sessions = self.load_sessions()
        if not sessions:
            return 0, ["No previous organization sessions found to undo."]

        base_resolved = self.base_folder.resolve()
        if is_critical_system_path(base_resolved):
            return 0, ["Security Alert: Refusing to operate on protected operating system directory."]

        last_session = sessions.pop()
        moves = last_session.get("moves", [])
        reverted_count = 0
        errors = []

        # Move files back in reverse order
        for record in reversed(moves):
            src = Path(record.get("target_path", ""))
            dest = Path(record.get("original_path", ""))

            # Security Defense 1: Path confinement check
            try:
                src_resolved = src.resolve()
                dest_resolved = dest.resolve()
            except (OSError, RuntimeError) as e:
                errors.append(f"Security Alert: Cannot resolve paths for rollback: {e}")
                continue

            try:
                is_src_safe = src_resolved.is_relative_to(base_resolved)
                is_dest_safe = dest_resolved.is_relative_to(base_resolved)
            except (AttributeError, ValueError):
                is_src_safe = False
                is_dest_safe = False

            if not (is_src_safe and is_dest_safe):
                errors.append(f"Security Alert: Blocked rollback out-of-bounds path '{dest}'")
                continue

            # Security Defense 2: Ensure destination is not a critical system path or symlink
            if is_critical_system_path(dest_resolved) or is_critical_system_path(src_resolved):
                errors.append(f"Security Alert: Blocked modification of protected system path '{dest}'")
                continue

            if src.is_symlink() or os.path.islink(src):
                errors.append(f"Security Alert: Refusing to follow symbolic link '{src}' during rollback.")
                continue

            if not src.exists():
                errors.append(f"Cannot restore '{dest.name}': file '{src}' no longer exists.")
                continue

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                reverted_count += 1
            except OSError as e:
                errors.append(f"Failed to move '{src}' back to '{dest}': {e}")

        # Clean up empty created directories
        self._cleanup_empty_dirs(self.base_folder)

        # Update journal atomically
        try:
            if sessions:
                self._atomic_write_sessions(sessions)
            else:
                if self.journal_path.exists():
                    self.journal_path.unlink()
        except OSError:
            pass

        return reverted_count, errors

    def _cleanup_empty_dirs(self, root: Path) -> None:
        """Recursively removes empty directories in the base folder, avoiding system roots."""
        root_resolved = root.resolve()
        if is_critical_system_path(root_resolved):
            return

        for dirpath, _, _ in os.walk(root, topdown=False):
            p = Path(dirpath)
            try:
                p_resolved = p.resolve()
                if p_resolved == root_resolved or not p_resolved.is_relative_to(root_resolved):
                    continue
            except (OSError, ValueError):
                continue

            if p.name.startswith("."):
                continue

            try:
                if not any(p.iterdir()):
                    p.rmdir()
            except OSError:
                pass
