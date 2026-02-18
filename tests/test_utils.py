import unittest
import tempfile
import shutil
import os
from pathlib import Path
from lisa.utils import find_project_root

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_find_root_with_lisa_dir(self):
        # Structure: /root/.lisa/
        root = Path(self.test_dir)
        (root / ".lisa").mkdir()
        
        found = find_project_root(str(root))
        self.assertEqual(found, str(root.resolve()))
        
    def test_find_root_from_subdir(self):
        # Structure: /root/.git/, /root/subdir/deep/
        root = Path(self.test_dir)
        (root / ".git").mkdir()
        subdir = root / "subdir" / "deep"
        subdir.mkdir(parents=True)

        found = find_project_root(str(subdir))
        self.assertEqual(found, str(root.resolve()))

    def test_fail_no_marker(self):
        # Structure: /root/ (no markers)
        with self.assertRaises(FileNotFoundError):
            find_project_root(self.test_dir)

if __name__ == '__main__':
    unittest.main()
