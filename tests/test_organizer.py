import unittest
import tempfile
import shutil
from pathlib import Path
from bytesift.core.organizer import Organizer, OrganizerConfig
from bytesift.core.transaction import TransactionManager

class TestOrganizer(unittest.TestCase):
    def test_full_organization_and_undo(self):
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create test files
            # 1. Invoice text file
            inv_file = temp_dir / "random_file_1.txt"
            inv_file.write_text("Invoice # 9999\nBill To: John\nTotal Due: $500", encoding="utf-8")

            # 2. Fake JPEG with magic bytes
            img_file = temp_dir / "unnamed_photo"
            img_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00someimagedata")

            # 3. Duplicate of the image
            img_copy = temp_dir / "another_photo"
            img_copy.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00someimagedata")

            # Setup Organizer
            config = OrganizerConfig(strategy="smart", detect_duplicates=True)
            organizer = Organizer(config)

            # 1. Generate plan
            plan = organizer.generate_plan(temp_dir)
            self.assertEqual(len(plan), 3)

            categories = [p.target_category for p in plan]
            self.assertIn("Documents/Invoices_Receipts", categories)
            self.assertIn("Images/JPEG", categories)
            self.assertIn("Duplicates", categories)

            # 2. Execute plan
            moved_count = organizer.execute_plan(temp_dir, plan)
            self.assertEqual(moved_count, 3)
            self.assertFalse(inv_file.exists())
            self.assertFalse(img_file.exists())
            self.assertFalse(img_copy.exists())

            # Check organized files exist (one in Images/JPEG, other in Duplicates)
            self.assertTrue((temp_dir / "Documents" / "Invoices_Receipts" / "random_file_1.txt").exists())
            images_moved = list((temp_dir / "Images" / "JPEG").iterdir())
            duplicates_moved = list((temp_dir / "Duplicates").iterdir())
            self.assertEqual(len(images_moved), 1)
            self.assertEqual(len(duplicates_moved), 1)

            # 3. Undo / Rollback
            tx_mgr = TransactionManager(temp_dir)
            reverted, errors = tx_mgr.undo_last_session()
            self.assertEqual(reverted, 3)
            self.assertEqual(len(errors), 0)

            # Files should be back in original locations
            self.assertTrue(inv_file.exists())
            self.assertTrue(img_file.exists())
            self.assertTrue(img_copy.exists())

        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()
