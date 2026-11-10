"""
ByteSift In-App Updater
Lightweight, zero-dependency update checker using GitHub Releases API.
Includes strict URL verification to prevent protocol hijacking or MITM redirects.
"""

from dataclasses import dataclass
import json
import platform
import re
import sys
from typing import List, Optional, Tuple
import urllib.error
import urllib.request

from bytesift import __version__

GITHUB_API_LATEST = "https://api.github.com/repos/PramudithaN/bytesift/releases/latest"
GITHUB_RELEASES_WEB = "https://github.com/PramudithaN/bytesift/releases/latest"
ALLOWED_UPDATE_PREFIXES = (
    "https://github.com/",
    "https://pramudithan.github.io/",
    "https://objects.githubusercontent.com/",
)

@dataclass
class UpdateInfo:
    current_version: str
    latest_version: str
    has_update: bool
    release_name: str
    release_notes: str
    html_url: str
    download_url: Optional[str] = None
    published_at: str = ""

def is_safe_update_url(url: Optional[str]) -> bool:
    """Verifies that an update URL strictly uses HTTPS and originates from trusted endpoints."""
    if not url or not isinstance(url, str):
        return False
    return any(url.startswith(prefix) for prefix in ALLOWED_UPDATE_PREFIXES)

def parse_version(v_str: str) -> Tuple[int, ...]:
    """
    Parses semantic version string into a comparable tuple of integers.
    Examples:
        'v0.1.0' -> (0, 1, 0)
        '0.2.1-beta' -> (0, 2, 1)
        '1.0' -> (1, 0, 0)
    """
    if not v_str:
        return (0, 0, 0)
    cleaned = v_str.strip().lstrip("vV")
    numbers = []
    for part in re.split(r"[.\-_]", cleaned):
        if part.isdigit():
            numbers.append(int(part))
        else:
            break
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers[:3])

def select_best_asset_url(assets: List[dict]) -> Optional[str]:
    """
    Finds the recommended binary asset URL for the user's operating system,
    prioritizing official installers (.exe installer on Windows, .dmg on macOS).
    """
    os_name = sys.platform.lower()

    # Pass 1: Prefer official desktop installers
    for asset in assets:
        name = asset.get("name", "").lower()
        url = asset.get("browser_download_url")
        if not is_safe_update_url(url):
            continue

        if os_name == "win32" and "setup" in name and name.endswith(".exe"):
            return url
        if os_name == "darwin" and name.endswith(".dmg"):
            return url

    # Pass 2: Fallback to standalone executables or portable archives
    for asset in assets:
        name = asset.get("name", "").lower()
        url = asset.get("browser_download_url")
        if not is_safe_update_url(url):
            continue

        if os_name == "win32":
            if name.endswith(".exe") or (name.endswith(".zip") and "windows" in name):
                return url
        elif os_name == "darwin":
            if name.endswith(".zip") and "macos" in name:
                return url
        else:  # Linux or other
            if name.endswith(".tar.gz") or name.endswith(".zip") or name.endswith(".appimage"):
                return url

    # Pass 3: Any validated asset
    for asset in assets:
        url = asset.get("browser_download_url")
        if is_safe_update_url(url):
            return url

    return None

def check_for_updates(current_version: str = __version__, timeout: float = 4.0) -> Optional[UpdateInfo]:
    """
    Queries GitHub Releases API for the latest published release.
    Returns UpdateInfo or None if network check fails or times out.
    """
    try:
        req = urllib.request.Request(
            GITHUB_API_LATEST,
            headers={
                "User-Agent": f"ByteSift/{current_version}",
                "Accept": "application/vnd.github.v3+json",
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))

        tag_name = data.get("tag_name", "")
        if not tag_name:
            return None

        clean_latest = tag_name.lstrip("vV")
        latest_tuple = parse_version(clean_latest)
        current_tuple = parse_version(current_version)

        has_update = latest_tuple > current_tuple

        raw_html_url = data.get("html_url")
        html_url = raw_html_url if is_safe_update_url(raw_html_url) else GITHUB_RELEASES_WEB
        release_name = data.get("name") or f"ByteSift v{clean_latest}"
        release_notes = data.get("body", "").strip()
        published_at = data.get("published_at", "")

        assets = data.get("assets", [])
        download_url = select_best_asset_url(assets) or html_url

        return UpdateInfo(
            current_version=current_version,
            latest_version=clean_latest,
            has_update=has_update,
            release_name=release_name,
            release_notes=release_notes,
            html_url=html_url,
            download_url=download_url,
            published_at=published_at,
        )

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError):
        return None
