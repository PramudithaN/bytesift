import unittest
from bytesift.ui.theme import (
    DARK_THEME,
    LIGHT_THEME,
    is_windows_dark_theme,
    enable_windows_dpi_awareness,
)

class TestTheme(unittest.TestCase):
    def test_theme_colors(self):
        self.assertEqual(DARK_THEME.name, "dark")
        self.assertEqual(LIGHT_THEME.name, "light")
        self.assertTrue(DARK_THEME.bg.startswith("#"))
        self.assertTrue(LIGHT_THEME.bg.startswith("#"))

    def test_windows_theme_detection(self):
        # Should return a boolean without throwing an exception
        res = is_windows_dark_theme()
        self.assertIsInstance(res, bool)

    def test_dpi_awareness_call(self):
        # Should execute safely on any platform
        enable_windows_dpi_awareness()

    def test_apply_fluent_theme(self):
        import tkinter as tk
        from bytesift.ui.theme import apply_fluent_theme
        try:
            r = tk.Tk()
            r.withdraw()
            apply_fluent_theme(r, DARK_THEME)
            apply_fluent_theme(r, LIGHT_THEME)
            r.destroy()
        except tk.TclError:
            # Headless CI environment without display
            pass

if __name__ == "__main__":
    unittest.main()
