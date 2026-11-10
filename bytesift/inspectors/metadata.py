"""
ByteSift Metadata Inspector
Extracts timestamp, date groups, and embedded metadata (e.g. EXIF) without external libraries.
Includes symlink isolation to prevent reading out-of-bounds files.
"""

from datetime import datetime
import os
from pathlib import Path
import re
from typing import Optional, Tuple

EXIF_DATE_PATTERN = re.compile(rb"\b(19\d\d|20\d\d):(\d\d):(\d\d)\s+(\d\d):(\d\d):(\d\d)\b")

def get_file_dates(filepath: Path) -> Tuple[datetime, str, str]:
    """
    Returns (datetime_obj, year_str, year_month_str) for the file.
    Prefers creation time (ctime on Windows) or modification time.
    """
    if filepath.is_symlink() or os.path.islink(filepath) or not filepath.is_file():
        now = datetime.now()
        return (now, now.strftime("%Y"), now.strftime("%Y-%m"))

    try:
        stat = filepath.stat()
        # On Windows, st_ctime is the file creation timestamp; on Linux it's metadata change
        timestamp = getattr(stat, "st_birthtime", None) or stat.st_ctime
        dt_c = datetime.fromtimestamp(timestamp)
        dt_m = datetime.fromtimestamp(stat.st_mtime)
        chosen_dt = min(dt_c, dt_m)
        return (chosen_dt, chosen_dt.strftime("%Y"), chosen_dt.strftime("%Y-%m"))
    except (OSError, PermissionError):
        now = datetime.now()
        return (now, now.strftime("%Y"), now.strftime("%Y-%m"))

def extract_jpeg_exif_date(filepath: Path) -> Optional[datetime]:
    """
    Lightweight zero-dependency JPEG EXIF parser for DateTimeOriginal (Tag 0x9003).
    Scans the APP1 segment without requiring Pillow/PExif.
    """
    if filepath.is_symlink() or os.path.islink(filepath) or not filepath.is_file():
        return None

    try:
        with open(filepath, "rb") as f:
            header = f.read(2)
            if header != b"\xff\xd8":
                return None

            while True:
                marker_header = f.read(4)
                if len(marker_header) < 4 or marker_header[0] != 0xFF:
                    break
                marker = marker_header[1]
                length = int.from_bytes(marker_header[2:4], "big")
                
                # APP1 marker (EXIF)
                if marker == 0xE1:
                    data = f.read(length - 2)
                    if data.startswith(b"Exif\x00\x00"):
                        # Search for ASCII date format: YYYY:MM:DD HH:MM:SS
                        raw = data[6:]
                        match = EXIF_DATE_PATTERN.search(raw)
                        if match:
                            date_str = match.group(0).decode("ascii")
                            return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    break
                else:
                    # Skip segment
                    f.seek(length - 2, os.SEEK_CUR)
    except (OSError, ValueError, IndexError):
        pass
    return None

def get_date_category(filepath: Path) -> Tuple[str, str]:
    """
    Determines year and year-month group for a file, using EXIF if JPEG, otherwise file stats.
    Returns (year, year_month).
    """
    if filepath.suffix.lower() in (".jpg", ".jpeg"):
        exif_dt = extract_jpeg_exif_date(filepath)
        if exif_dt:
            return (exif_dt.strftime("%Y"), exif_dt.strftime("%Y-%m"))

    _, year, ym = get_file_dates(filepath)
    return (year, ym)
