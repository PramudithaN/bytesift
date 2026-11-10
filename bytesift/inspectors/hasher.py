"""
ByteSift Hasher Inspector
Ultra-fast file hashing for duplicate detection and content integrity.
Includes symlink isolation and multi-tier signature optimization.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List

CHUNK_SIZE = 65536  # 64 KB

def calculate_file_hash(filepath: Path, algorithm: str = "sha256") -> str:
    """Calculates hash of a file streaming in chunks to prevent memory spikes."""
    if filepath.is_symlink() or os.path.islink(filepath) or not filepath.is_file():
        return ""

    try:
        hasher = hashlib.new(algorithm)
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return ""

def quick_signature_hash(filepath: Path) -> str:
    """
    Very fast fingerprint for large files: size + first 8KB + last 8KB.
    Allows rapidly spotting potential duplicates before computing a full hash.
    """
    if filepath.is_symlink() or os.path.islink(filepath) or not filepath.is_file():
        return ""

    try:
        stat_res = filepath.stat()
        size = stat_res.st_size
        if size <= 16384:
            return calculate_file_hash(filepath, "md5")

        hasher = hashlib.md5()
        hasher.update(str(size).encode("ascii"))
        with open(filepath, "rb") as f:
            hasher.update(f.read(8192))
            f.seek(-8192, 2)
            hasher.update(f.read(8192))
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return ""

def find_duplicate_groups(filepaths: List[Path]) -> Dict[str, List[Path]]:
    """
    Finds duplicate files in a list of paths using a 3-pass strategy:
    1. Group by file size.
    2. Quick signature hash on candidate collisions.
    3. Full SHA-256 hash only for signature collisions.
    """
    by_size: Dict[int, List[Path]] = {}
    for path in filepaths:
        if path.is_symlink() or os.path.islink(path) or not path.is_file():
            continue
        try:
            sz = path.stat().st_size
            by_size.setdefault(sz, []).append(path)
        except (OSError, PermissionError):
            continue

    duplicates: Dict[str, List[Path]] = {}
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue

        # Pass 2: Quick signature filter for candidates larger than 16KB
        if size > 16384:
            by_sig: Dict[str, List[Path]] = {}
            for cand in candidates:
                sig = quick_signature_hash(cand)
                if sig:
                    by_sig.setdefault(sig, []).append(cand)
            filtered_groups = [grp for grp in by_sig.values() if len(grp) > 1]
        else:
            filtered_groups = [candidates]

        # Pass 3: Full SHA-256 hash on verified collision candidates
        for group in filtered_groups:
            hashes: Dict[str, List[Path]] = {}
            for cand in group:
                h = calculate_file_hash(cand, "sha256")
                if h:
                    hashes.setdefault(h, []).append(cand)

            for h, matches in hashes.items():
                if len(matches) > 1:
                    duplicates[h] = matches

    return duplicates
