import tempfile
import unittest
from pathlib import Path
from bytesift.inspectors.hasher import calculate_file_hash, quick_signature_hash, find_duplicate_groups

class TestHasher(unittest.TestCase):
    def test_calculate_file_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello world")
            path = Path(f.name)
        try:
            h = calculate_file_hash(path, "sha256")
            self.assertEqual(h, "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9")
        finally:
            path.unlink()

    def test_quick_signature_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"sample" * 50)
            path = Path(f.name)
        try:
            h = quick_signature_hash(path)
            self.assertTrue(len(h) > 0)
        finally:
            path.unlink()

    def test_find_duplicate_groups(self):
        with tempfile.NamedTemporaryFile(delete=False) as f1, tempfile.NamedTemporaryFile(delete=False) as f2:
            f1.write(b"identical")
            f2.write(b"identical")
            p1, p2 = Path(f1.name), Path(f2.name)
        try:
            groups = find_duplicate_groups([p1, p2])
            self.assertEqual(len(groups), 1)
        finally:
            p1.unlink()
            p2.unlink()

if __name__ == "__main__":
    unittest.main()
