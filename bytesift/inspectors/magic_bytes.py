"""
ByteSift Magic Bytes Inspector
Examines raw initial bytes to determine true file formats independent of extensions.
"""

from pathlib import Path
from typing import Optional, Tuple
import zipfile
import zlib

# Fixed-offset magic byte signatures
# Format: (signature_bytes, category, subcategory)
STATIC_SIGNATURES: list[Tuple[bytes, str, str]] = [
    # Creative & Design
    (b"8BPS", "Design", "Photoshop"),
    (b"\x06\x06\xed\xf5\xd8\x1d\x46\xe5\xbd\x31\xef\xe7\xfe\x74\xb7\x1d", "Design", "InDesign"),
    (b"fig-kiwi", "Design", "Figma"),

    # 3D & Animation
    (b"BLENDER", "3D_Models", "Blender"),
    (b"Kaydara FBX Binary  \x00\x1a\x00", "3D_Models", "FBX"),
    (b"glTF", "3D_Models", "GLTF"),

    # Game Development
    (b"UnityFS", "Game_Development", "Unity"),
    (b"UnityRaw", "Game_Development", "Unity"),
    (b"UnityWeb", "Game_Development", "Unity"),
    (b"UnityArchive", "Game_Development", "Unity"),

    # Audio Projects / DAWs
    (b"FLhd", "Audio_Projects", "FL_Studio"),

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
    (b"{\\rtf1", "Documents", "RTF"),

    # Audio
    (b"ID3", "Audio", "MP3"),
    (b"fLaC", "Audio", "FLAC"),
    (b"OggS", "Audio", "OGG"),
    (b"MThd", "Audio", "MIDI"),

    # Video & Containers
    (b"FLV\x01", "Videos", "FLV"),
    (b"\x30\x26\xb2\x75\x8e\x66\xcf\x11\xa6\xd9\x00\xaa\x00\x62\xce\x6c", "Videos", "WMV"),
    (b"\x00\x00\x01\xba", "Videos", "MPEG_VOB"),
    (b"\x00\x00\x01\xb3", "Videos", "MPEG"),
    (b".RMF", "Videos", "RealMedia"),

    # Archives & Compressed
    (b"7z\xbc\xaf\x27\x1c", "Archives", "7-Zip"),
    (b"Rar!\x1a\x07\x00", "Archives", "RAR"),
    (b"Rar!\x1a\x07\x01\x00", "Archives", "RAR"),
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
    """Inspects RIFF headers (WAV, AVI, WebP, After Effects projects)."""
    if len(header) >= 12 and header.startswith(b"RIFF"):
        subtype = header[8:12]
        if subtype in (b"Egg!", b"FXFX", b"AEDP"):
            return ("Video_Projects", "After_Effects")
        if subtype == b"WEBP":
            return ("Images", "WebP")
        if subtype == b"WAVE":
            return ("Audio", "WAV")
        if subtype == b"AVI ":
            return ("Videos", "AVI")
    return None

def check_ftyp_format(header: bytes) -> Optional[Tuple[str, str]]:
    """Inspects ISO base media file formats (MP4, M4A, MOV, HEIC, 3GP)."""
    if len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12]
        if brand in (b"M4A ", b"M4B "):
            return ("Audio", "M4A")
        if brand in (b"heic", b"mif1", b"msf1", b"heix"):
            return ("Images", "HEIC")
        if brand in (b"qt  ", b"mqt "):
            return ("Videos", "MOV")
        if brand in (b"3gp4", b"3gp5", b"3gp6", b"3g2a", b"3ge6"):
            return ("Videos", "3GP")
        return ("Videos", "MP4")
    # QuickTime MOV atom headers without leading ftyp
    if len(header) >= 8 and header[4:8] in (b"moov", b"mdat", b"wide", b"free", b"skip", b"pnot"):
        return ("Videos", "MOV")
    return None

def check_matroska_format(header: bytes) -> Optional[Tuple[str, str]]:
    """Distinguishes Matroska MKV from WebM."""
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        if b"webm" in header.lower():
            return ("Videos", "WebM")
        return ("Videos", "MKV")
    return None

def check_pdf_or_illustrator(header: bytes, filepath: Path) -> Tuple[str, str]:
    """
    Distinguishes Adobe Illustrator (.ai) files from standard PDF / PostScript documents.
    """
    ext = filepath.suffix.lower()
    if ext in (".ai", ".ait"):
        return ("Design", "Illustrator")

    try:
        with open(filepath, "rb") as f:
            sample = f.read(4096)
        if any(marker in sample for marker in (
            b"Adobe Illustrator",
            b"AIPrivateData",
            b"Creator: Adobe Illustrator",
            b"%%Creator: (Adobe Illustrator"
        )):
            return ("Design", "Illustrator")
    except (OSError, PermissionError):
        pass

    if header.startswith(b"%!PS"):
        return ("Documents", "PostScript")
    return ("Documents", "PDF")

def inspect_gzip_format(filepath: Path) -> Tuple[str, str]:
    """
    Inspects GZIP streams to identify Premiere Pro projects (.prproj),
    Ableton Live sets (.als), or Unity packages (.unitypackage).
    """
    ext = filepath.suffix.lower()
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        decompressed = decompressor.decompress(chunk, 4096)
        if any(marker in decompressed for marker in (b"<PremiereData", b"<Project ObjectID=", b"Adobe Premiere")):
            return ("Video_Projects", "Premiere_Pro")
        if b"<Ableton" in decompressed:
            return ("Audio_Projects", "Ableton")
    except Exception:
        pass

    if ext in (".prproj", ".prel", ".mogrt"):
        return ("Video_Projects", "Premiere_Pro")
    if ext == ".unitypackage":
        return ("Game_Development", "Unity")
    if ext == ".als":
        return ("Audio_Projects", "Ableton")
    return ("Archives", "GZip")

def inspect_zip_based_format(filepath: Path) -> Tuple[str, str]:
    """
    Inspects ZIP container contents to distinguish DOCX, XLSX, PPTX, EPUB,
    DaVinci Resolve projects, CapCut drafts, InDesign IDML, Sketch, Figma, or general ZIP.
    """
    ext = filepath.suffix.lower()
    if ext in (".drp", ".drt", ".dra", ".drb"):
        return ("Video_Projects", "DaVinci_Resolve")
    if ext in (".capcut", ".ccproj", ".ccv"):
        return ("Video_Projects", "CapCut")
    if ext == ".idml":
        return ("Design", "InDesign")
    if ext == ".fig":
        return ("Design", "Figma")
    if ext == ".sketch":
        return ("Design", "Sketch")

    try:
        with zipfile.ZipFile(filepath, "r") as z:
            namelist = set(z.namelist())
            lower_names = {n.lower() for n in namelist}

            # DaVinci Resolve project check
            if any(name in lower_names for name in ("project.xml", "project/project.xml")):
                try:
                    for xml_name in ("project.xml", "Project.xml", "project/project.xml"):
                        if xml_name in namelist:
                            sample = z.read(xml_name)[:2048]
                            if any(k in sample for k in (b"Sm2Project", b"Resolve", b"DaVinci", b"timeline", b"Timeline")):
                                return ("Video_Projects", "DaVinci_Resolve")
                except Exception:
                    pass

            # CapCut project draft check
            if any(name in lower_names for name in ("draft_info.json", "draft_content.json")):
                return ("Video_Projects", "CapCut")

            # Adobe InDesign IDML check
            if "designmap.xml" in lower_names:
                return ("Design", "InDesign")

            # Sketch app check
            if "document.json" in lower_names and "meta.json" in lower_names:
                return ("Design", "Sketch")

            # EPUB check
            if "mimetype" in namelist:
                try:
                    mime = z.read("mimetype").decode("utf-8", errors="ignore").strip()
                    if "epub" in mime:
                        return ("Documents", "EPUB")
                    if "indesign" in mime:
                        return ("Design", "InDesign")
                except (OSError, UnicodeDecodeError):
                    pass
            if "META-INF/container.xml" in namelist:
                return ("Documents", "EPUB")

            # Office documents
            if "word/document.xml" in namelist:
                return ("Documents", "Word_DOCX")
            if "xl/workbook.xml" in namelist:
                return ("Documents", "Excel_XLSX")
            if "ppt/presentation.xml" in namelist:
                return ("Documents", "PowerPoint_PPTX")
    except (zipfile.BadZipFile, OSError, KeyError):
        pass
    return ("Archives", "ZIP")

def inspect_magic_bytes(filepath: Path) -> Optional[Tuple[str, str]]:
    """
    Reads the initial bytes of a file to determine category and subcategory.
    Returns (category, subcategory) or None if unknown.
    """
    try:
        with open(filepath, "rb") as f:
            header = f.read(64)
    except (OSError, PermissionError):
        return None

    if not header:
        return ("Empty", "ZeroByte")

    # 1. PDF vs Illustrator check
    if header.startswith(b"%PDF-") or header.startswith(b"%!PS"):
        return check_pdf_or_illustrator(header, filepath)

    # 2. Matroska vs WebM
    mkv_match = check_matroska_format(header)
    if mkv_match:
        return mkv_match

    # 3. Direct static prefix match
    for signature, category, subcategory in STATIC_SIGNATURES:
        if header.startswith(signature):
            return (category, subcategory)

    # 4. Check GZIP container sub-types (Premiere Pro, Ableton, Unity)
    if header.startswith(b"\x1f\x8b"):
        return inspect_gzip_format(filepath)

    # 5. Check ZIP package sub-types (DOCX / XLSX / PPTX / EPUB / DaVinci / CapCut / InDesign)
    if header.startswith(b"PK\x03\x04"):
        return inspect_zip_based_format(filepath)

    # 6. Check RIFF formats (AVI, WAV, WebP, After Effects)
    riff_match = check_riff_format(header)
    if riff_match:
        return riff_match

    # 7. Check ftyp formats (MP4, MOV, M4A, HEIC, 3GP)
    ftyp_match = check_ftyp_format(header)
    if ftyp_match:
        return ftyp_match

    # 8. Check MPEG Transport Stream (.ts, .m2ts) sync byte
    if header.startswith(b"\x47") and filepath.suffix.lower() in (".ts", ".m2ts", ".mts"):
        return ("Videos", "MPEG_TS")

    return None
