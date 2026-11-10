"""
ByteSift Text Heuristics Inspector
Fast regex and keyword frequency scoring for text files and plain documents.
Includes symlink isolation to prevent reading out-of-bounds files.
"""

import os
from pathlib import Path
import re
from typing import Optional, Tuple

# Sample size in bytes (reading first 8KB is lightning fast and sufficient for categorization)
SAMPLE_SIZE = 8192

# Rule definitions: (category, subcategory, list_of_keywords, minimum_matches, regex_bonus)
TEXT_RULES: list[Tuple[str, str, list[str], int, Optional[re.Pattern]]] = [
    # Invoices & Receipts
    (
        "Documents",
        "Invoices_Receipts",
        [
            "invoice", "receipt", "total due", "bill to", "tax invoice",
            "subtotal", "vat reg", "payment due", "amount payable", "remit to"
        ],
        2,
        re.compile(r"(invoice\s*(#|no|number)|total\s*:\s*[\$\€\£\₹]?[0-9]+)", re.IGNORECASE)
    ),
    # Resumes & CVs
    (
        "Documents",
        "Resumes_CVs",
        [
            "curriculum vitae", "work experience", "professional experience",
            "education", "skills", "summary of qualifications", "employment history",
            "certifications", "career objective"
        ],
        2,
        re.compile(r"(curriculum\s+vitae|resume\b)", re.IGNORECASE)
    ),
    # Legal & Contracts
    (
        "Documents",
        "Legal_Contracts",
        [
            "agreement", "non-disclosure", "confidentiality", "governing law",
            "terms and conditions", "indemnification", "severability", "parties hereto"
        ],
        2,
        re.compile(r"(non-disclosure\s+agreement|this\s+agreement\s+is\s+entered)", re.IGNORECASE)
    ),
    # Source Code: Python
    (
        "Code",
        "Python",
        ["def ", "import ", "from ", "class ", "self.", "return ", "elif ", "except "],
        3,
        re.compile(r"(if\s+__name__\s*==\s*['\"]__main__['\"]|def\s+[a-zA-Z0-9_]+\s*\(.*?\)\s*:)")
    ),
    # Source Code: JS / TS
    (
        "Code",
        "JavaScript_TypeScript",
        ["const ", "let ", "function ", "export ", "import ", "interface ", "return ", "console.log"],
        3,
        re.compile(r"(export\s+(default\s+)?(function|class|const)|import\s+.*\s+from\s+['\"])")
    ),
    # Source Code: HTML / Web
    (
        "Code",
        "Web_HTML",
        ["<!doctype html>", "<html", "<head>", "<body", "<div", "<script", "<meta "],
        2,
        re.compile(r"<!doctype\s+html>|<html(\s+[^>]*>|>)", re.IGNORECASE)
    ),
    # Source Code: CSS
    (
        "Code",
        "Styles_CSS",
        ["display:", "margin:", "padding:", "color:", "background:", "@media", ":root"],
        3,
        re.compile(r"(\.[a-zA-Z0-9_-]+\s*\{|[a-zA-Z0-9_-]+\s*:\s*[^;]+;)")
    ),
    # Source Code: SQL
    (
        "Code",
        "SQL",
        ["select ", "insert into", "update ", "delete from", "create table", "primary key", "where "],
        2,
        re.compile(r"\b(SELECT\s+.*\s+FROM|CREATE\s+TABLE)\b", re.IGNORECASE)
    ),
    # Source Code: Shell / Bash / PowerShell
    (
        "Code",
        "Scripts_Shell",
        ["#!/bin/bash", "#!/bin/sh", "echo ", "powershell", "set-location", "get-childitem", "chmod +x"],
        2,
        re.compile(r"^#!\s*/bin/(bash|sh|zsh)", re.MULTILINE)
    ),
    # Log files
    (
        "Logs",
        "System_Logs",
        ["[info]", "[error]", "[warn]", "[debug]", "[fatal]", "traceback", "exception:", "timestamp"],
        3,
        re.compile(r"(\[\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}|(INFO|ERROR|WARN|DEBUG)\s*[:\]])")
    ),
    # Documentation & Markdown Notes
    (
        "Documents",
        "Markdown_Notes",
        ["# ", "## ", "### ", "```", "---", "- [ ]", "- [x]"],
        2,
        re.compile(r"^#{1,3}\s+[a-zA-Z0-9]+", re.MULTILINE)
    ),
    # Game Development: Unity YAML (Scenes, Prefabs, Assets)
    (
        "Game_Development",
        "Unity",
        ["tag:unity3d.com", "monobehaviour:", "gameobject:", "transform:", "prefabinstance:"],
        2,
        re.compile(r"(%TAG\s+!u!\s+tag:unity3d\.com|--- !u!\d+ &\d+)", re.IGNORECASE)
    ),
    # Video Projects: CapCut Drafts & JSON
    (
        "Video_Projects",
        "CapCut",
        ["draft_materials", "canvas_config", "draft_fold_path", "draft_id", "capcut", "draft_timeline"],
        2,
        re.compile(r"(\"draft_materials\"|\"canvas_config\"|\"capcut\")", re.IGNORECASE)
    ),
    # Video Projects: Adobe After Effects XML Project (.aepx)
    (
        "Video_Projects",
        "After_Effects",
        ["aftereffectsproject", "adobe after effects", "bparam", "pinpoint", "composition"],
        2,
        re.compile(r"(<AfterEffectsProject|<string>Adobe After Effects)", re.IGNORECASE)
    ),
    # Video Projects: DaVinci Resolve Timeline / Project XML
    (
        "Video_Projects",
        "DaVinci_Resolve",
        ["davinci resolve", "davinci", "resolveversion", "sm2project", "timeline"],
        2,
        re.compile(r"(<DaVinciResolve|<xmeml|<fcpxml|ResolveVersion)", re.IGNORECASE)
    ),
    # Videos: Subtitles
    (
        "Videos",
        "Subtitles",
        ["-->", "dialogue:", "format: layered", "style: default", "webvtt"],
        1,
        re.compile(r"(^\d+\r?\n\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}|WEBVTT|\[Script Info\])", re.MULTILINE)
    ),
    # Videos: Playlists (M3U / M3U8)
    (
        "Videos",
        "Playlists",
        ["#extm3u", "#extinf:", "#ext-x-targetduration", "<playlist", "#ext-x-stream-inf"],
        1,
        re.compile(r"^#EXTM3U", re.MULTILINE)
    ),
    # 3D Models: Wavefront OBJ
    (
        "3D_Models",
        "Wavefront_OBJ",
        ["# wavefront obj", "mtllib ", "usemtl ", "vt ", "vn "],
        2,
        re.compile(r"^(v\s+[-0-9\.]+|vn\s+[-0-9\.]+|f\s+\d+/\d+)", re.MULTILINE)
    ),
    # 3D Models: STL (ASCII format)
    (
        "3D_Models",
        "STL",
        ["solid ", "facet normal", "outer loop", "vertex ", "endloop", "endfacet", "endsolid"],
        3,
        re.compile(r"^solid\s+.*?\s+facet\s+normal", re.DOTALL | re.IGNORECASE)
    ),
]

def is_text_file(filepath: Path) -> bool:
    """Checks if a file is plain text by reading a small chunk and checking byte values."""
    if filepath.is_symlink() or os.path.islink(filepath) or not filepath.is_file():
        return False

    try:
        with open(filepath, "rb") as f:
            chunk = f.read(1024)
        if not chunk:
            return True
        # If there are null bytes, it's almost certainly binary
        if b"\x00" in chunk:
            return False
        # Try UTF-8 decode
        try:
            chunk.decode("utf-8")
            return True
        except UnicodeDecodeError:
            # Fallback check printable ASCII ratio
            printable = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
            return (printable / len(chunk)) > 0.85
    except (OSError, PermissionError):
        return False

def inspect_text_content(filepath: Path) -> Optional[Tuple[str, str]]:
    """
    Scans the beginning of a text file and scores it against known content patterns.
    Returns (category, subcategory) or None.
    """
    if not is_text_file(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(SAMPLE_SIZE)
    except (OSError, PermissionError):
        return None

    if not text.strip():
        return ("Documents", "Empty_Text")

    lower_text = text.lower()
    best_candidate: Optional[Tuple[str, str]] = None
    highest_score = 0

    for category, subcategory, keywords, threshold, regex in TEXT_RULES:
        # Count keyword hits
        matches = sum(1 for kw in keywords if kw in lower_text)
        
        # Regex bonus
        bonus = 0
        if regex and regex.search(text):
            bonus = 3

        total_score = matches + bonus

        if matches >= threshold and total_score > highest_score:
            highest_score = total_score
            best_candidate = (category, subcategory)

    if best_candidate:
        return best_candidate

    return ("Documents", "General_Text")
