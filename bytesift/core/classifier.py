"""
ByteSift Core Classifier
Coordinates magic byte detection, text heuristics, and fallback mechanisms.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from bytesift.inspectors.magic_bytes import inspect_magic_bytes
from bytesift.inspectors.text_heuristics import inspect_text_content, is_text_file
from bytesift.inspectors.metadata import get_date_category

# Extension fallback mapping for files where magic bytes are absent or general (e.g. text/config)
EXTENSION_FALLBACK = {
    # Documents
    ".txt": ("Documents", "Plain_Text"),
    ".md": ("Documents", "Markdown_Notes"),
    ".csv": ("Documents", "Data_CSV"),
    ".pdf": ("Documents", "PDF"),
    ".docx": ("Documents", "Word_DOCX"),
    ".xlsx": ("Documents", "Excel_XLSX"),
    ".pptx": ("Documents", "PowerPoint_PPTX"),

    # Code
    ".py": ("Code", "Python"),
    ".js": ("Code", "JavaScript"),
    ".ts": ("Code", "TypeScript"),
    ".jsx": ("Code", "React_JSX"),
    ".tsx": ("Code", "React_TSX"),
    ".html": ("Code", "Web_HTML"),
    ".css": ("Code", "Styles_CSS"),
    ".cpp": ("Code", "CPP"),
    ".c": ("Code", "C"),
    ".rs": ("Code", "Rust"),
    ".go": ("Code", "Go"),
    ".java": ("Code", "Java"),
    ".sql": ("Code", "SQL"),
    ".sh": ("Code", "Shell"),
    ".bat": ("Code", "Batch"),
    ".ps1": ("Code", "PowerShell"),

    # Config & Data
    ".json": ("Config", "JSON"),
    ".yaml": ("Config", "YAML"),
    ".yml": ("Config", "YAML"),
    ".toml": ("Config", "TOML"),
    ".xml": ("Config", "XML"),
    ".ini": ("Config", "INI"),
    ".env": ("Config", "ENV"),

    # Media
    ".png": ("Images", "PNG"),
    ".jpg": ("Images", "JPEG"),
    ".jpeg": ("Images", "JPEG"),
    ".svg": ("Images", "SVG"),
    ".gif": ("Images", "GIF"),
    ".webp": ("Images", "WebP"),
    ".mp3": ("Audio", "MP3"),
    ".wav": ("Audio", "WAV"),
    ".mp4": ("Videos", "MP4"),
    ".mkv": ("Videos", "MKV"),

    # Archives
    ".zip": ("Archives", "ZIP"),
    ".rar": ("Archives", "RAR"),
    ".7z": ("Archives", "7-Zip"),
    ".tar": ("Archives", "TAR"),
    ".gz": ("Archives", "GZip"),
}

@dataclass
class Classification:
    category: str
    subcategory: str
    method: str  # "magic_bytes", "text_heuristics", "extension_fallback", "unknown"
    confidence: float

    @property
    def folder_path(self) -> str:
        """Returns relative folder name like 'Documents/Invoices_Receipts'."""
        if self.subcategory:
            return f"{self.category}/{self.subcategory}"
        return self.category

class Classifier:
    def __init__(self, enable_content_heuristics: bool = True):
        self.enable_content_heuristics = enable_content_heuristics

    def classify(self, filepath: Path) -> Classification:
        """
        Classifies a single file using the multi-tiered offline inspection pipeline.
        """
        # Tier 1: Magic Bytes Check
        magic = inspect_magic_bytes(filepath)
        if magic:
            category, subcategory = magic
            # If it's a general text or markdown file, or unknown doc, we can still refine with heuristics
            if not (category == "Documents" and subcategory in ("Plain_Text", "ZeroByte")):
                # Check if it's text despite magic (some files like SVG or HTML might trigger basic)
                return Classification(category, subcategory, "magic_bytes", 0.95)

        # Tier 2: Text Content Heuristic Inspection
        if self.enable_content_heuristics and is_text_file(filepath):
            text_match = inspect_text_content(filepath)
            if text_match:
                cat, subcat = text_match
                if subcat != "General_Text":
                    return Classification(cat, subcat, "text_heuristics", 0.90)

        # Tier 3: Extension Fallback
        ext = filepath.suffix.lower()
        if ext in EXTENSION_FALLBACK:
            cat, subcat = EXTENSION_FALLBACK[ext]
            return Classification(cat, subcat, "extension_fallback", 0.70)

        # If magic matched general document, keep it
        if magic:
            return Classification(magic[0], magic[1], "magic_bytes", 0.60)

        return Classification("Unclassified", "Misc", "unknown", 0.10)
