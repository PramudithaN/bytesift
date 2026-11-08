import unittest
import tempfile
from pathlib import Path
from bytesift.inspectors.magic_bytes import inspect_magic_bytes

class TestMagicBytes(unittest.TestCase):
    def test_detect_jpeg(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00")
            f_path = Path(f.name)
        try:
            res = inspect_magic_bytes(f_path)
            self.assertEqual(res, ("Images", "JPEG"))
        finally:
            f_path.unlink()

    def test_detect_pdf(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"%PDF-1.7\n%some content here")
            f_path = Path(f.name)
        try:
            res = inspect_magic_bytes(f_path)
            self.assertEqual(res, ("Documents", "PDF"))
        finally:
            f_path.unlink()

    def test_detect_png(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
            f_path = Path(f.name)
        try:
            res = inspect_magic_bytes(f_path)
            self.assertEqual(res, ("Images", "PNG"))
        finally:
            f_path.unlink()

    def test_detect_empty(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f_path = Path(f.name)
        try:
            res = inspect_magic_bytes(f_path)
            self.assertEqual(res, ("Empty", "ZeroByte"))
        finally:
            f_path.unlink()

if __name__ == "__main__":
    unittest.main()
