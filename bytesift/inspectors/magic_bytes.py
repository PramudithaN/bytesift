"""
ByteSift Magic Bytes Inspector
Examines raw initial bytes to determine true file formats independent of extensions.
"""

from pathlib import Path
from typing import Optional, Tuple
import zipfile

# Fixed-offset magic byte signatures
# Format: (signature_bytes, category, subcategory)
STATIC_SIGNATURES: list[Tuple[bytes, str, str]] = [
    # Images
    (b"\xff\xd8\xff", "Images", "JPEG"),
    (b"\x89PNG\r\n\x1a\n", "Images", "PNG"),
    (b"GIF87a", "Images", "GIF"),
    (b"GIF89a", "Images", "GIF"),
    (b"BM", "Images", "Bitmap"),
    (b"\x00\x00\x01\x00", "Images", "Icons"),
    (b"II*\x00", "Images", "TIFF"),
    (b"MM\x00*", "Images", "TIFF"),

    # Documents & Reading
    (b"%PDF-", "Documents", "PDF"),
    (b"{\\rtf1", "Documents", "RTF"),
    (b"%!PS", "Documents", "PostScript"),

    # Audio
    (b"ID3", "Audio", "MP3"),
    (b"fLaC", "Audio", "FLAC"),
    (b"OggS", "Audio", "OGG"),
    (b"MThd", "Audio", "MIDI"),

    # Video & Containers
    (b"\x1a\x45\xdf\xa3", "Videos", "MKV_WebM"),
    (b"FLV\x01", "Videos", "FLV"),

    # Archives & Compressed
    (b"7z\xbc\xaf\x27\x1c", "Archives", "7-Zip"),
    (b"Rar!\x1a\x07\x00", "Archives", "RAR"),
    (b"Rar!\x1a\x07\x01\x00", "Archives", "RAR"),
    (b"\x1f\x8b", "Archives", "GZip"),
    (b"BZh", "Archives", "BZip2"),
    (b"\xfd7zXZ\x00", "Archives", "XZ"),

    # Executables / Binaries
    (b"MZ", "Executables", "Windows_EXE_DLL"),
    (b"\x7fELF", "Executables", "Linux_ELF"),
    (b"\xfe\xed\xfa\xce", "Executables", "Mach-O"),
    (b"\xfe\xed\xfa\xcf", "Executables", "Mach-O"),
    (b"\xce\xfa\xed\xfe", "Executables", "Mach-O"),
    (b"\xcf\xfa\xed\xfe", "Executables", "Mach-O"),

    # Databases
    (b"SQLite format 3\x00", "Databases", "SQLite"),

    # Fonts
    (b"wOFF", "Fonts", "WOFF"),
    (b"wOF2", "Fonts", "WOFF2"),
    (b"OTTO", "Fonts", "OpenType"),
    (b"\x00\x01\x00\x00", "Fonts", "TrueType"),
]

def check_riff_format(header: bytes) -> Optional[Tuple[str, str]]:
    """Inspects RIFF headers (WAV, AVI, WebP)."""
    if len(header) >= 12 and header.startswith(b"RIFF"):
        subtype = header[8:12]
        if subtype == b"WEBP":
            return ("Images", "WebP")
        if subtype == b"WAVE":
            return ("Audio", "WAV")
        if subtype == b"AVI ":
            return ("Videos", "AVI")
    return None

def check_ftyp_format(header: bytes) -> Optional[Tuple[str, str]]:
    """Inspects ISO base media file formats (MP4, M4A, MOV, HEIC)."""
    if len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12]
        if brand in (b"M4A ", b"M4B "):
            return ("Audio", "M4A")
        if brand in (b"heic", b"mif1", b"msf1", b"heix"):
            return ("Images", "HEIC")
        return ("Videos", "MP4")
    return None

def inspect_zip_based_format(filepath: Path) -> Tuple[str, str]:
    """Inspects ZIP container contents to distinguish DOCX, XLSX, PPTX, EPUB, or general ZIP."""
    try:
        with zipfile.ZipFile(filepath, "r") as z:
            namelist = set(z.namelist())
            if "mimetype" in namelist:
                try:
                    mime = z.read("mimetype").decode("utf-8", errors="ignore").strip()
                    if "epub" in mime:
                        return ("Documents", "EPUB")
                except Exception:
                    pass
            if "word/document.xml" in namelist:
                return ("Documents", "Word_DOCX")
            if "xl/workbook.xml" in namelist:
                return ("Documents", "Excel_XLSX")
            if "ppt/presentation.xml" in namelist:
                return ("Documents", "PowerPoint_PPTX")
            if "META-INF/container.xml" in namelist:
                return ("Documents", "EPUB")
    except Exception:
        pass
    return ("Archives", "ZIP")

def inspect_magic_bytes(filepath: Path) -> Optional[Tuple[str, str]]:
    """
    Reads the initial 64 bytes of a file to determine category and subcategory.
    Returns (category, subcategory) or None if unknown.
    """
    try:
        with open(filepath, "rb") as f:
            header = f.read(64)
    except (OSError, PermissionError):
        return None

    if not header:
        return ("Empty", "ZeroByte")

    # 1. Direct static prefix match
    for signature, category, subcategory in STATIC_SIGNATURES:
        if header.startswith(signature):
            return (category, subcategory)

    # 2. Check ZIP package sub-types (DOCX / XLSX / PPTX / EPUB)
    if header.startswith(b"PK\x03\x04"):
        return inspect_zip_based_format(filepath)

    # 3. Check RIFF formats
    riff_match = check_riff_format(header)
    if riff_match:
        return riff_match

    # 4. Check ftyp formats (MP4, M4A, HEIC)
    ftyp_match = check_ftyp_format(header)
    if ftyp_match:
        return ftyp_match

    return None
