import unittest
import tempfile
import shutil
import os
from pathlib import Path
from scripts.lisa.analysis import find_importers, get_module_name

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for the project
        self.test_dir = tempfile.mkdtemp()
        self.project_root = self.test_dir
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def create_file(self, rel_path, content):
        file_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def test_get_module_name(self):
        # Test module name resolution
        self.create_file("pkg/module.py", "")
        module_name = get_module_name(os.path.join(self.test_dir, "pkg/module.py"), self.project_root)
        self.assertEqual(module_name, "pkg.module")
        
    def test_find_direct_import(self):
        # target: lib/core.py -> lib.core
        # importer: app.py -> "import lib.core"
        self.create_file("lib/core.py", "# core logic")
        self.create_file("app.py", "import lib.core\n")
        
        importers = find_importers(os.path.join(self.test_dir, "lib/core.py"), self.project_root)
        self.assertIn("app.py", importers)
        
    def test_find_from_import(self):
        # target: utils.py -> utils
        # importer: main.py -> "from utils import helper"
        self.create_file("utils.py", "def helper(): pass")
        self.create_file("main.py", "from utils import helper\n")
        
        importers = find_importers(os.path.join(self.test_dir, "utils.py"), self.project_root)
        self.assertIn("main.py", importers)

    def test_no_import(self):
        self.create_file("target.py", "")
        self.create_file("other.py", "import os\n")
        
        importers = find_importers(os.path.join(self.test_dir, "target.py"), self.project_root)
        self.assertEqual(importers, [])

    def test_skip_self_import(self):
        # A file shouldn't be considered an importer of itself even if it has circular deps logic
        self.create_file("mod.py", "import mod\n") 
        importers = find_importers(os.path.join(self.test_dir, "mod.py"), self.project_root)
        self.assertEqual(importers, [])

if __name__ == '__main__':
    unittest.main()
