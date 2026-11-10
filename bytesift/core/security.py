"""
ByteSift Security & System Protection Guardrails
Enforces strict boundaries to ensure system files and OS directories are never
accessed, modified, or relocated, and prevents path traversal or symlink attacks.
"""

import os
from pathlib import Path
import stat
import sys
from typing import Set, Tuple

WIN32_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Critical Unix and macOS directory trees that must never be targeted or modified
UNIX_CRITICAL_DIRS = {
    "/bin", "/sbin", "/boot", "/dev", "/etc", "/lib", "/lib32", "/lib64",
    "/libx32", "/lost+found", "/proc", "/root", "/run", "/sys", "/usr", "/var",
    "/System", "/Library", "/Applications"
}

def get_protected_system_paths() -> Set[Path]:
    """Returns resolved paths of OS-critical system directory trees."""
    protected: Set[Path] = set()

    if sys.platform == "win32":
        # System directory trees
        env_vars = [
            "SystemRoot", "WinDir", "ProgramFiles", "ProgramFiles(x86)",
            "ProgramData", "CommonProgramFiles", "CommonProgramFiles(x86)"
        ]
        for var in env_vars:
            val = os.environ.get(var)
            if val:
                protected.add(Path(val).resolve())

        # Fallback common Windows system locations
        for fallback in [
            r"C:\Windows", r"C:\Windows\System32", r"C:\Program Files",
            r"C:\Program Files (x86)", r"C:\ProgramData", r"C:\Recovery"
        ]:
            p = Path(fallback)
            if p.exists():
                protected.add(p.resolve())
    else:
        for u_dir in UNIX_CRITICAL_DIRS:
            p = Path(u_dir)
            if p.exists():
                protected.add(p.resolve())

    return protected

def is_critical_system_path(path: Path) -> bool:
    """
    Checks if path is an OS-critical directory, a drive root, or inside system files.
    """
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        return True

    # 1. Drive or filesystem root (e.g. C:\ or / or D:\)
    if resolved == resolved.parent:
        return True

    # 2. Specific OS protected system trees (e.g. C:\Windows, C:\Program Files, /etc)
    protected = get_protected_system_paths()
    for prot in protected:
        if resolved == prot:
            return True
        try:
            if resolved.is_relative_to(prot):
                return True
        except (AttributeError, ValueError):
            pass

    return False

def is_safe_target_directory(folder: Path) -> Tuple[bool, str]:
    """
    Validates that a directory is safe to scan or organize.
    Ensures no system root or OS directory is targeted.
    """
    try:
        resolved = folder.resolve()
    except Exception as e:
        return False, f"Invalid directory path: {e}"

    if not resolved.exists():
        return False, f"Directory does not exist: {folder}"

    if not resolved.is_dir():
        return False, f"Path is not a directory: {folder}"

    if is_critical_system_path(resolved):
        return False, f"Access Denied: Protected operating system location: {folder}"

    # Verify write access to target directory
    if not os.access(resolved, os.W_OK | os.R_OK):
        return False, f"Permission Denied: Directory is not writable: {folder}"

    return True, ""

def is_safe_file_to_process(file: Path, root: Path) -> bool:
    """
    Validates that a file is safe to read, hash, and move.
    Excludes symlinks, junctions, Windows device names, system/hidden files, and out-of-bounds paths.
    """
    try:
        # 1. Never follow symlinks or junction points
        if file.is_symlink() or os.path.islink(file):
            return False

        # 2. Must be a regular file
        if not file.is_file():
            return False

        # 3. Path confinement: must be inside root
        resolved = file.resolve()
        root_resolved = root.resolve()
        if not resolved.is_relative_to(root_resolved):
            return False

        # 4. Windows reserved device names (e.g. CON, PRN, AUX, NUL)
        if sys.platform == "win32":
            if file.stem.upper() in WIN32_RESERVED_NAMES or file.name.upper() in WIN32_RESERVED_NAMES:
                return False

            # Check hidden/system attributes
            try:
                attrs = getattr(file.stat(), "st_file_attributes", 0)
                if attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM):
                    return False
            except (OSError, PermissionError):
                return False

        # 5. Must have explicit read and write permissions
        if not (os.access(file, os.R_OK) and os.access(file, os.W_OK)):
            return False

        return True
    except (OSError, PermissionError, ValueError):
        return False
