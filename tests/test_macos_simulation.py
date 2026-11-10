"""
ByteSift macOS Platform Simulation Test
Simulates macOS (sys.platform == 'darwin') on any operating system to verify
all Apple-specific UI code paths, menu bar generation, shortcuts, and theme resolvers.
"""

import sys
import unittest
import urllib.request
from unittest.mock import patch, MagicMock
from pathlib import Path

# Pre-import modules so sys.modules has them cached before sys.platform mocking
import bytesift.ui.theme as b_theme
import bytesift.ui.gui as b_gui

class TestMacOSSimulation(unittest.TestCase):
    def test_macos_theme_detection_logic(self):
        with patch("sys.platform", "darwin"), patch("subprocess.run") as mock_sub:
            # Case 1: Dark Mode reported by macOS defaults
            mock_sub.return_value = MagicMock(returncode=0, stdout="Dark\n")
            self.assertTrue(b_theme.is_macos_dark_theme())
            self.assertTrue(b_theme.is_system_dark_theme())

            # Case 2: Light Mode (defaults returns non-zero / "The domain/default pair does not exist")
            mock_sub.return_value = MagicMock(returncode=1, stdout="")
            self.assertFalse(b_theme.is_macos_dark_theme())
            self.assertFalse(b_theme.is_system_dark_theme())

    def test_macos_system_fonts(self):
        with patch("sys.platform", "darwin"):
            font = b_theme.get_system_font(11, bold=True)
            self.assertEqual(font[0], ".AppleSystemUIFont")
            self.assertEqual(font[1], 11)
            self.assertEqual(font[2], "bold")

    def test_macos_gui_menus_and_shortcuts(self):
        """Tests that Tkinter menu bars, Command shortcuts, and buttons initialize without error."""
        import tkinter as tk
        with patch("sys.platform", "darwin"), patch("bytesift.ui.gui.is_system_dark_theme", return_value=True):
            try:
                root = tk.Tk()
                root.withdraw()
                app = b_gui.ByteSiftApp(root)

                # Verify native macOS menus are attached
                self.assertIsNotNone(root["menu"])

                # Verify Command/Mod keyboard shortcuts are bound
                bindings = root.bind()
                self.assertTrue(any("Key-o" in b for b in bindings))

                root.destroy()
            except tk.TclError:
                # Headless environments
                pass

    def test_macos_finder_reveal_command(self):
        """Verifies that on macOS, 'open' is called instead of 'explorer'."""
        with patch("sys.platform", "darwin"), \
             patch("bytesift.ui.gui.is_system_dark_theme", return_value=False), \
             patch("subprocess.Popen") as mock_popen:
            import tkinter as tk
            try:
                root = tk.Tk()
                root.withdraw()
                app = b_gui.ByteSiftApp(root)
                app.selected_folder.set(str(Path(".").resolve()))
                app.on_open_in_explorer()
                mock_popen.assert_called_once()
                args = mock_popen.call_args[0][0]
                self.assertEqual(args[0], "open")
                root.destroy()
            except tk.TclError:
                pass

if __name__ == "__main__":
    unittest.main()
