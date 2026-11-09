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
    # Creative & Design (Photoshop, Illustrator, InDesign, Figma, etc.)
    ".psd": ("Design", "Photoshop"),
    ".psb": ("Design", "Photoshop"),
    ".abr": ("Design", "Photoshop"),
    ".atn": ("Design", "Photoshop"),
    ".pat": ("Design", "Photoshop"),
    ".csh": ("Design", "Photoshop"),
    ".aco": ("Design", "Photoshop"),
    ".ase": ("Design", "Photoshop"),
    ".ai": ("Design", "Illustrator"),
    ".ait": ("Design", "Illustrator"),
    ".eps": ("Design", "Illustrator"),
    ".indd": ("Design", "InDesign"),
    ".indt": ("Design", "InDesign"),
    ".idml": ("Design", "InDesign"),
    ".fig": ("Design", "Figma"),
    ".sketch": ("Design", "Sketch"),
    ".xd": ("Design", "Adobe_XD"),
    ".cdr": ("Design", "CorelDraw"),

    # Video Projects & Editing (After Effects, Premiere Pro, DaVinci Resolve, CapCut, etc.)
    ".prproj": ("Video_Projects", "Premiere_Pro"),
    ".prel": ("Video_Projects", "Premiere_Pro"),
    ".mogrt": ("Video_Projects", "Premiere_Pro"),
    ".aep": ("Video_Projects", "After_Effects"),
    ".aet": ("Video_Projects", "After_Effects"),
    ".aepx": ("Video_Projects", "After_Effects"),
    ".drp": ("Video_Projects", "DaVinci_Resolve"),
    ".drt": ("Video_Projects", "DaVinci_Resolve"),
    ".dra": ("Video_Projects", "DaVinci_Resolve"),
    ".drb": ("Video_Projects", "DaVinci_Resolve"),
    ".capcut": ("Video_Projects", "CapCut"),
    ".ccproj": ("Video_Projects", "CapCut"),
    ".ccv": ("Video_Projects", "CapCut"),
    ".fcpxml": ("Video_Projects", "Final_Cut_Pro"),
    ".fcproject": ("Video_Projects", "Final_Cut_Pro"),
    ".fcp": ("Video_Projects", "Final_Cut_Pro"),
    ".veg": ("Video_Projects", "Sony_Vegas"),
    ".camproj": ("Video_Projects", "Camtasia"),
    ".tscproj": ("Video_Projects", "Camtasia"),

    # 3D & Animation (Blender, Cinema 4D, Maya, 3ds Max, FBX, OBJ, STL, etc.)
    ".blend": ("3D_Models", "Blender"),
    ".blend1": ("3D_Models", "Blender"),
    ".blend2": ("3D_Models", "Blender"),
    ".blend3": ("3D_Models", "Blender"),
    ".c4d": ("3D_Models", "Cinema_4D"),
    ".max": ("3D_Models", "3ds_Max"),
    ".3ds": ("3D_Models", "3ds_Max"),
    ".mb": ("3D_Models", "Maya"),
    ".ma": ("3D_Models", "Maya"),
    ".fbx": ("3D_Models", "FBX"),
    ".obj": ("3D_Models", "Wavefront_OBJ"),
    ".mtl": ("3D_Models", "Wavefront_OBJ"),
    ".stl": ("3D_Models", "STL"),
    ".gltf": ("3D_Models", "GLTF"),
    ".glb": ("3D_Models", "GLTF"),
    ".dae": ("3D_Models", "Collada"),
    ".step": ("3D_Models", "CAD"),
    ".stp": ("3D_Models", "CAD"),
    ".iges": ("3D_Models", "CAD"),
    ".igs": ("3D_Models", "CAD"),
    ".dwg": ("3D_Models", "CAD"),
    ".dxf": ("3D_Models", "CAD"),

    # Game Development (Unity, Unreal Engine, Godot)
    ".unity": ("Game_Development", "Unity"),
    ".unitypackage": ("Game_Development", "Unity"),
    ".prefab": ("Game_Development", "Unity"),
    ".asset": ("Game_Development", "Unity"),
    ".unityscene": ("Game_Development", "Unity"),
    ".uproject": ("Game_Development", "Unreal_Engine"),
    ".uasset": ("Game_Development", "Unreal_Engine"),
    ".umap": ("Game_Development", "Unreal_Engine"),
    ".godot": ("Game_Development", "Godot"),
    ".tscn": ("Game_Development", "Godot"),
    ".tres": ("Game_Development", "Godot"),

    # Video Player Formats & Media
    ".mp4": ("Videos", "MP4"),
    ".m4v": ("Videos", "MP4"),
    ".mov": ("Videos", "MOV"),
    ".qt": ("Videos", "MOV"),
    ".mkv": ("Videos", "MKV"),
    ".avi": ("Videos", "AVI"),
    ".wmv": ("Videos", "WMV"),
    ".asf": ("Videos", "WMV"),
    ".flv": ("Videos", "FLV"),
    ".webm": ("Videos", "WebM"),
    ".vob": ("Videos", "MPEG_VOB"),
    ".mpg": ("Videos", "MPEG"),
    ".mpeg": ("Videos", "MPEG"),
    ".m2v": ("Videos", "MPEG"),
    ".ts": ("Videos", "MPEG_TS"),
    ".m2ts": ("Videos", "MPEG_TS"),
    ".mts": ("Videos", "MPEG_TS"),
    ".3gp": ("Videos", "3GP"),
    ".3g2": ("Videos", "3GP"),
    ".ogv": ("Videos", "OGV"),
    ".rm": ("Videos", "RealMedia"),
    ".rmvb": ("Videos", "RealMedia"),
    ".divx": ("Videos", "DivX"),

    # Subtitles & Playlists (Video Player companions)
    ".srt": ("Videos", "Subtitles"),
    ".vtt": ("Videos", "Subtitles"),
    ".ass": ("Videos", "Subtitles"),
    ".ssa": ("Videos", "Subtitles"),
    ".sub": ("Videos", "Subtitles"),
    ".idx": ("Videos", "Subtitles"),
    ".m3u": ("Videos", "Playlists"),
    ".m3u8": ("Videos", "Playlists"),
    ".pls": ("Videos", "Playlists"),
    ".xspf": ("Videos", "Playlists"),
    ".wpl": ("Videos", "Playlists"),

    # Audio Projects / DAWs
    ".flp": ("Audio_Projects", "FL_Studio"),
    ".als": ("Audio_Projects", "Ableton"),
    ".aup3": ("Audio_Projects", "Audacity"),
    ".logicx": ("Audio_Projects", "Logic_Pro"),
    ".band": ("Audio_Projects", "GarageBand"),
    ".cpr": ("Audio_Projects", "Cubase"),

    # Documents
    ".txt": ("Documents", "Plain_Text"),
    ".md": ("Documents", "Markdown_Notes"),
    ".csv": ("Documents", "Data_CSV"),
    ".pdf": ("Documents", "PDF"),
    ".docx": ("Documents", "Word_DOCX"),
    ".xlsx": ("Documents", "Excel_XLSX"),
    ".pptx": ("Documents", "PowerPoint_PPTX"),
    ".epub": ("Documents", "EPUB"),
    ".rtf": ("Documents", "RTF"),

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

    # Media: Images
    ".png": ("Images", "PNG"),
    ".jpg": ("Images", "JPEG"),
    ".jpeg": ("Images", "JPEG"),
    ".svg": ("Images", "SVG"),
    ".gif": ("Images", "GIF"),
    ".webp": ("Images", "WebP"),
    ".bmp": ("Images", "Bitmap"),
    ".ico": ("Images", "Icons"),
    ".tiff": ("Images", "TIFF"),
    ".tif": ("Images", "TIFF"),
    ".heic": ("Images", "HEIC"),

    # Media: Audio
    ".mp3": ("Audio", "MP3"),
    ".wav": ("Audio", "WAV"),
    ".flac": ("Audio", "FLAC"),
    ".ogg": ("Audio", "OGG"),
    ".m4a": ("Audio", "M4A"),
    ".aac": ("Audio", "AAC"),
    ".mid": ("Audio", "MIDI"),
    ".midi": ("Audio", "MIDI"),

    # Archives
    ".zip": ("Archives", "ZIP"),
    ".rar": ("Archives", "RAR"),
    ".7z": ("Archives", "7-Zip"),
    ".tar": ("Archives", "TAR"),
    ".gz": ("Archives", "GZip"),
    ".bz2": ("Archives", "BZip2"),
    ".xz": ("Archives", "XZ"),
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
