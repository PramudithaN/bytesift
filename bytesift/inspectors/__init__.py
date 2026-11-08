"""
ByteSift Inspectors
"""
from .magic_bytes import inspect_magic_bytes
from .text_heuristics import inspect_text_content, is_text_file
from .metadata import get_date_category
from .hasher import calculate_file_hash, find_duplicate_groups

__all__ = [
    "inspect_magic_bytes",
    "inspect_text_content",
    "is_text_file",
    "get_date_category",
    "calculate_file_hash",
    "find_duplicate_groups",
]
