"""
Unit tests for ByteSift in-app updater and version checking mechanism.
"""

import io
import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from bytesift.core.updater import (
    parse_version,
    select_best_asset_url,
    check_for_updates,
    UpdateInfo,
)

class TestUpdater(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("0.1.0"), (0, 1, 0))
        self.assertEqual(parse_version("v0.1.0"), (0, 1, 0))
        self.assertEqual(parse_version("V1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("0.2"), (0, 2, 0))
        self.assertEqual(parse_version("v2.0.1-rc1"), (2, 0, 1))

        # Comparisons
        self.assertGreater(parse_version("v0.2.0"), parse_version("v0.1.0"))
        self.assertGreater(parse_version("v0.1.1"), parse_version("v0.1.0"))
        self.assertGreater(parse_version("v1.0.0"), parse_version("v0.9.9"))
        self.assertEqual(parse_version("v0.1.0"), parse_version("0.1.0"))

    def test_select_best_asset_url(self):
        assets = [
            {"name": "ByteSift-Windows-x64.zip", "browser_download_url": "https://github.com/.../win.zip"},
            {"name": "ByteSift-Setup-x64.exe", "browser_download_url": "https://github.com/.../setup.exe"},
            {"name": "ByteSift-macOS-Universal.dmg", "browser_download_url": "https://github.com/.../mac.dmg"},
        ]

        # Windows preference
        with patch("sys.platform", "win32"):
            win_url = select_best_asset_url(assets)
            self.assertEqual(win_url, "https://github.com/.../setup.exe")

        # macOS preference
        with patch("sys.platform", "darwin"):
            mac_url = select_best_asset_url(assets)
            self.assertEqual(mac_url, "https://github.com/.../mac.dmg")

    @patch("urllib.request.urlopen")
    def test_check_for_updates_available(self, mock_urlopen):
        mock_payload = {
            "tag_name": "v0.2.0",
            "name": "ByteSift v0.2.0 - Major Feature Update",
            "body": "Added detection for creative apps and in-app updater.",
            "html_url": "https://github.com/PramudithaN/bytesift/releases/tag/v0.2.0",
            "assets": [
                {
                    "name": "ByteSift-Setup-x64.exe",
                    "browser_download_url": "https://github.com/PramudithaN/bytesift/releases/download/v0.2.0/ByteSift-Setup-x64.exe",
                }
            ],
        }
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        info = check_for_updates(current_version="0.1.0")
        self.assertIsNotNone(info)
        self.assertTrue(info.has_update)
        self.assertEqual(info.latest_version, "0.2.0")
        self.assertEqual(info.current_version, "0.1.0")
        self.assertIn("v0.2.0", info.release_name)
        self.assertIn("ByteSift-Setup-x64.exe", info.download_url)

    @patch("urllib.request.urlopen")
    def test_check_for_updates_already_latest(self, mock_urlopen):
        mock_payload = {
            "tag_name": "v0.1.0",
            "name": "ByteSift v0.1.0",
            "body": "Initial release",
            "html_url": "https://github.com/PramudithaN/bytesift/releases/tag/v0.1.0",
            "assets": [],
        }
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        info = check_for_updates(current_version="0.1.0")
        self.assertIsNotNone(info)
        self.assertFalse(info.has_update)
        self.assertEqual(info.latest_version, "0.1.0")

    @patch("urllib.request.urlopen")
    def test_check_for_updates_offline(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("No route to host")
        info = check_for_updates(current_version="0.1.0")
        self.assertIsNone(info)

if __name__ == "__main__":
    unittest.main()
