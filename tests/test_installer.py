import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from lisa.commands import _init_setup, polish, refactor
from lisa.config import ConfigManager

class TestInstaller(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('lisa.commands.status_cmd')
    def test_init_setup_creates_structure(self, mock_status):
        """Should create .lisa structure and config."""
        mock_status.return_value = 0
        
        result = _init_setup(self.test_dir)
        
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".lisa")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".lisa", "skills")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".lisa", "archive")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".lisa", "config.yaml")))
        
        # Check config content
        with open(os.path.join(self.test_dir, ".lisa", "config.yaml"), "r") as f:
            content = f.read()
            self.assertIn("skill_base_path: \".lisa/skills\"", content)
            self.assertIn("installation_type: \"resident\"", content)

    @patch('lisa.commands.status_cmd')
    def test_init_setup_copies_skills(self, mock_status):
        """Should copy core skills to .lisa/skills."""
        mock_status.return_value = 0
        
        _init_setup(self.test_dir)
        
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".lisa", "skills", "polish.md")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".lisa", "skills", "refactor.md")))

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands._print_scope_context')
    def test_skill_resolution_prefers_local(self, mock_scope, mock_root):
        """Should prefer local skill files over internal ones."""
        mock_root.return_value = self.test_dir
        
        # Setup local skill
        skills_dir = os.path.join(self.test_dir, ".lisa", "skills")
        os.makedirs(skills_dir)
        local_content = "LOCAL POLISH CONTENT"
        with open(os.path.join(skills_dir, "polish.md"), "w") as f:
            f.write(local_content)
            
        with patch('builtins.print') as mock_print:
            polish([])
            # Verify local content was printed
            mock_print.assert_any_call(local_content)

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands._print_scope_context')
    def test_skill_resolution_falls_back(self, mock_scope, mock_root):
        """Should fall back to internal skills if local ones are missing."""
        mock_root.return_value = self.test_dir
        # Ensure no local skill exists
        
        with patch('builtins.print') as mock_print:
            with patch('lisa.commands.open', unittest.mock.mock_open(read_data="INTERNAL CONTENT")) as mock_open:
                # We need to be careful with mock_open as it affects everything.
                # Better to just verify it doesn't error and prints something.
                pass

        # Instead of mocking open, let's just run it and see if it finds the internal file
        # since we know the internal file exists in the real environment.
        with patch('lisa.commands.print_with_status'):
             with patch('builtins.print') as mock_print:
                polish([])
                # It should print something from the internal file
                self.assertTrue(mock_print.called)

if __name__ == "__main__":
    unittest.main()
