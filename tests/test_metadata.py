import tempfile
import unittest
from pathlib import Path
from bytesift.inspectors.metadata import get_file_dates, get_date_category

class TestMetadata(unittest.TestCase):
    def test_get_file_dates(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"data")
            path = Path(f.name)
        try:
            dt, year, ym = get_file_dates(path)
            self.assertIsNotNone(dt)
            self.assertTrue(year.isdigit())
            self.assertEqual(len(year), 4)
            self.assertIn("-", ym)
        finally:
            path.unlink()

    def test_get_date_category(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            path = Path(f.name)
        try:
            year, ym = get_date_category(path)
            self.assertTrue(year.isdigit())
            self.assertEqual(len(ym), 7)
        finally:
            path.unlink()

if __name__ == "__main__":
    unittest.main()
