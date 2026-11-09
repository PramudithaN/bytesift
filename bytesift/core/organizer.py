"""
ByteSift Organizer Engine
Generates execution plans, previews organization actions, and safely executes moves.
"""

from dataclasses import dataclass
from pathlib import Path
import logging
import os
import shutil
import stat
import sys
from typing import Callable, List, Optional, Set
from bytesift.core.classifier import Classifier, Classification
from bytesift.core.transaction import TransactionManager, FileMoveRecord
from bytesift.inspectors.hasher import find_duplicate_groups
from bytesift.inspectors.metadata import get_date_category

logger = logging.getLogger(__name__)

DEFAULT_IGNORED_NAMES: Set[str] = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".venv", "venv",
    ".bytesift_history.json", "desktop.ini", ".DS_Store", "Thumbs.db",
    ".localized", ".Trashes", ".fseventsd", ".Spotlight-V100"
}

@dataclass
class PlanItem:
    source: Path
    target_category: str
    target_path: Path
    method: str
    is_duplicate: bool = False
    original_of_duplicate: Optional[Path] = None

@dataclass
class OrganizerConfig:
    strategy: str = "smart"  # "smart", "date", "type"
    group_by_date: bool = False
    detect_duplicates: bool = True
    recursive: bool = False
    ignored_names: Optional[Set[str]] = None

def resolve_target_collision(dest: Path, used_destinations: Set[Path]) -> Path:
    """
    Ensures dest does not overwrite an existing file on disk or an earlier file
    scheduled for the same path in the current plan.
    Appends ' (1)', ' (2)' before extension.
    """
    candidate = dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while candidate.exists() or candidate in used_destinations:
        candidate = dest.with_name(f"{stem} ({counter}){suffix}")
        counter += 1
    used_destinations.add(candidate)
    return candidate

class Organizer:
    def __init__(self, config: Optional[OrganizerConfig] = None):
        self.config = config or OrganizerConfig()
        self.ignored = self.config.ignored_names or DEFAULT_IGNORED_NAMES
        self.classifier = Classifier(enable_content_heuristics=(self.config.strategy in ("smart", "heuristics")))

    def scan_files(self, folder: Path) -> List[Path]:
        """Collects files in folder, respecting recursive flag and ignore list."""
        collected: List[Path] = []
        if self.config.recursive:
            for item in folder.rglob("*"):
                if item.is_file() and not self._is_ignored(item, folder):
                    collected.append(item)
        else:
            for item in folder.iterdir():
                if item.is_file() and not self._is_ignored(item, folder):
                    collected.append(item)
        return collected

    def _is_ignored(self, item: Path, root: Path) -> bool:
        """
        Determines if a file or any of its parents is in the ignored list.
        Safely ignores OS-hidden/system files and anti-ransomware EDR canary bait decoys.
        """
        name = item.name
        if name in self.ignored or name.startswith(".") or name.startswith("._"):
            return True

        # Safety filter: Ignore EDR / Antivirus canary bait patterns (e.g. Cortex XDR / CrowdStrike)
        if name.startswith("!!!!!") or name.startswith("ZZZZZ") or name.startswith("XORXOR"):
            return True

        # Safety filter: Ignore Windows Hidden and System files
        if sys.platform == "win32":
            try:
                attrs = getattr(item.stat(), "st_file_attributes", 0)
                if attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM):
                    return True
            except (OSError, PermissionError):
                return True

        for part in item.relative_to(root).parts[:-1]:
            if part in self.ignored or part.startswith(".") or part.startswith("._"):
                return True
        return False

    def generate_plan(self, folder: Path, progress_cb: Optional[Callable[[int, int], None]] = None) -> List[PlanItem]:
        """
        Builds the complete execution plan without modifying any files.
        """
        files = self.scan_files(folder)
        total = len(files)
        plan: List[PlanItem] = []
        used_destinations: Set[Path] = set()

        # Step 1: Detect duplicate files if enabled
        duplicate_map = {}
        if self.config.detect_duplicates and total > 1:
            dup_groups = find_duplicate_groups(files)
            for file_hash, group in dup_groups.items():
                original = group[0]
                for copy in group[1:]:
                    duplicate_map[copy] = original

        # Step 2: Classify and calculate destination paths
        for idx, file in enumerate(files):
            if progress_cb:
                progress_cb(idx + 1, total)

            # Check duplicate first
            if file in duplicate_map:
                category = "Duplicates"
                method = "sha256_duplicate"
                target_dir = folder / category
                target_dest = resolve_target_collision(target_dir / file.name, used_destinations)
                plan.append(PlanItem(
                    source=file,
                    target_category=category,
                    target_path=target_dest,
                    method=method,
                    is_duplicate=True,
                    original_of_duplicate=duplicate_map[file]
                ))
                continue

            # Strategy: Date-first
            if self.config.strategy == "date":
                _, ym = get_date_category(file)
                category = f"Timeline/{ym}"
                method = "date_metadata"
            else:
                classification = self.classifier.classify(file)
                category = classification.folder_path
                method = classification.method

                # Optional secondary grouping by date (e.g. Images/JPEG/2024-05)
                if self.config.group_by_date and classification.category in ("Images", "Videos"):
                    _, ym = get_date_category(file)
                    category = f"{category}/{ym}"

            target_dir = folder / category
            target_dest = resolve_target_collision(target_dir / file.name, used_destinations)

            # Only add to plan if source != destination
            if file.resolve() != target_dest.resolve():
                plan.append(PlanItem(
                    source=file,
                    target_category=category,
                    target_path=target_dest,
                    method=method,
                    is_duplicate=False
                ))

        return plan

    def execute_plan(self, folder: Path, plan: List[PlanItem]) -> int:
        """
        Executes the plan by moving files and journaling every move for rollback.
        Returns the number of files successfully moved.
        """
        if not plan:
            return 0

        transaction_mgr = TransactionManager(folder)
        records: List[FileMoveRecord] = []
        moved_count = 0

        for item in plan:
            try:
                item.target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item.source), str(item.target_path))
                records.append(FileMoveRecord(
                    original_path=str(item.source.resolve()),
                    target_path=str(item.target_path.resolve())
                ))
                moved_count += 1
            except (OSError, shutil.Error) as e:
                logger.error("Failed to move %s -> %s: %s", item.source.name, item.target_path, e)

        transaction_mgr.save_session(records)
        return moved_count
