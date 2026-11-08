import tempfile
import unittest
from pathlib import Path
from bytesift.core.classifier import Classifier, Classification

class TestClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = Classifier()

    def test_extension_fallback(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b"{}")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertIsInstance(result, Classification)
            self.assertEqual(result.category, "Config")
            self.assertEqual(result.subcategory, "JSON")
            self.assertEqual(result.folder_path, "Config/JSON")
        finally:
            path.unlink()

    def test_unknown_file(self):
        with tempfile.NamedTemporaryFile(suffix=".unknownext123", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\x04")
            path = Path(f.name)
        try:
            result = self.classifier.classify(path)
            self.assertEqual(result.category, "Unclassified")
        finally:
            path.unlink()

if __name__ == "__main__":
    unittest.main()
