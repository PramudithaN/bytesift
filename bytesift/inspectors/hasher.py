"""
ByteSift Hasher Inspector
Ultra-fast file hashing for duplicate detection and content integrity.
"""

import hashlib
from pathlib import Path
from typing import Dict, List

CHUNK_SIZE = 65536  # 64 KB

def calculate_file_hash(filepath: Path, algorithm: str = "sha256") -> str:
    """Calculates hash of a file streaming in chunks to prevent memory spikes."""
    hasher = hashlib.new(algorithm)
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""

def quick_signature_hash(filepath: Path) -> str:
    """
    Very fast fingerprint for large files: size + first 8KB + last 8KB.
    Allows rapidly spotting potential duplicates before computing a full hash.
    """
    try:
        stat = filepath.stat()
        size = stat.st_size
        if size <= 16384:
            return calculate_file_hash(filepath, "md5")

        hasher = hashlib.md5()
        hasher.update(str(size).encode("ascii"))
        with open(filepath, "rb") as f:
            hasher.update(f.read(8192))
            f.seek(-8192, 2)
            hasher.update(f.read(8192))
        return hasher.hexdigest()
    except Exception:
        return ""

def find_duplicate_groups(filepaths: List[Path]) -> Dict[str, List[Path]]:
    """
    Finds duplicate files in a list of paths using a 2-pass strategy:
    1. Group by file size.
    2. Full hash only for size collisions.
    """
    by_size: Dict[int, List[Path]] = {}
    for path in filepaths:
        try:
            sz = path.stat().st_size
            by_size.setdefault(sz, []).append(path)
        except Exception:
            continue

    duplicates: Dict[str, List[Path]] = {}
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue
        hashes: Dict[str, List[Path]] = {}
        for cand in candidates:
            h = calculate_file_hash(cand, "sha256")
            if h:
                hashes.setdefault(h, []).append(cand)

        for h, matches in hashes.items():
            if len(matches) > 1:
                duplicates[h] = matches

    return duplicates
