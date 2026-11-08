"""
ByteSift Transaction & History Log
Maintains a local journal of moved files for one-click rollback (Undo).
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import shutil
from typing import List, Optional, Tuple

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

    def save_session(self, moves: List[FileMoveRecord]) -> None:
        """Appends a new organization session to the journal."""
        if not moves:
            return

        sessions = self.load_sessions()
        session = SessionRecord(
            timestamp=datetime.now().isoformat(),
            base_folder=str(self.base_folder.resolve()),
            moves=[asdict(m) for m in moves]
        )
        sessions.append(asdict(session))

        try:
            with open(self.journal_path, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2)
        except OSError as e:
            logger.warning("Failed to write undo journal: %s", e)

    def load_sessions(self) -> List[dict]:
        """Loads previous sessions from the journal file."""
        if not self.journal_path.exists():
            return []
        try:
            with open(self.journal_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    def undo_last_session(self) -> Tuple[int, List[str]]:
        """
        Reverts the most recent session's file moves.
        Returns (num_reverted, list_of_errors).
        """
        sessions = self.load_sessions()
        if not sessions:
            return 0, ["No previous organization sessions found to undo."]

        last_session = sessions.pop()
        moves = last_session.get("moves", [])
        reverted_count = 0
        errors = []

        # Move files back in reverse order
        for record in reversed(moves):
            src = Path(record["target_path"])
            dest = Path(record["original_path"])

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

        # Update journal
        try:
            if sessions:
                with open(self.journal_path, "w", encoding="utf-8") as f:
                    json.dump(sessions, f, indent=2)
            else:
                if self.journal_path.exists():
                    self.journal_path.unlink()
        except OSError:
            pass

        return reverted_count, errors

    def _cleanup_empty_dirs(self, root: Path) -> None:
        """Recursively removes empty directories in the base folder."""
        for dirpath, _, _ in os.walk(root, topdown=False):
            p = Path(dirpath)
            if p == root or p.name.startswith("."):
                continue
            try:
                if not any(p.iterdir()):
                    p.rmdir()
            except OSError:
                pass
