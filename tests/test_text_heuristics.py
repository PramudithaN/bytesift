import unittest
import tempfile
from pathlib import Path
from bytesift.inspectors.text_heuristics import inspect_text_content, is_text_file

class TestTextHeuristics(unittest.TestCase):
    def test_detect_invoice(self):
        content = "INVOICE # 10492\nBill To: Acme Corp\nTotal Due: $1,250.00\nPayment Due in 30 days."
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write(content)
            f_path = Path(f.name)
        try:
            self.assertTrue(is_text_file(f_path))
            res = inspect_text_content(f_path)
            self.assertEqual(res, ("Documents", "Invoices_Receipts"))
        finally:
            f_path.unlink()

    def test_detect_resume(self):
        content = "CURRICULUM VITAE\nJohn Doe\nProfessional Experience:\nSoftware Engineer (2020-2024)\nEducation:\nB.Sc Computer Science"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write(content)
            f_path = Path(f.name)
        try:
            res = inspect_text_content(f_path)
            self.assertEqual(res, ("Documents", "Resumes_CVs"))
        finally:
            f_path.unlink()

    def test_detect_python_code(self):
        content = "import os\nfrom pathlib import Path\n\ndef main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write(content)
            f_path = Path(f.name)
        try:
            res = inspect_text_content(f_path)
            self.assertEqual(res, ("Code", "Python"))
        finally:
            f_path.unlink()

if __name__ == "__main__":
    unittest.main()
