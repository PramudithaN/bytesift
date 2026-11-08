import io
import sys
import tempfile
import unittest
from pathlib import Path
from bytesift.cli import main

class TestCLI(unittest.TestCase):
    def test_cli_scan(self):
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "invoice.txt"
        test_file.write_text("Invoice # 123\nTotal Due: $100\nBill To: Client", encoding="utf-8")

        captured = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured
            sys.argv = ["bytesift", "scan", str(temp_dir)]
            main()
        finally:
            sys.stdout = old_stdout
            test_file.unlink()
            temp_dir.rmdir()

        output = captured.getvalue()
        self.assertIn("Found 1 file(s) to organize", output)

    def test_cli_organize_dry_run(self):
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "doc.txt"
        test_file.write_text("Regular text file", encoding="utf-8")

        captured = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured
            sys.argv = ["bytesift", "organize", str(temp_dir), "--dry-run"]
            main()
        finally:
            sys.stdout = old_stdout
            test_file.unlink()
            temp_dir.rmdir()

        output = captured.getvalue()
        self.assertIn("[DRY RUN]", output)

if __name__ == "__main__":
    unittest.main()
