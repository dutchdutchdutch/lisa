
import unittest
import os
import json
import shutil
import tempfile
import time
from unittest.mock import patch, MagicMock

# Adjust path to import scripts
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.lisa.archiver import archive_session, reset_session
from scripts.lisa.state import StateManager

class TestSessionArchival(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for test environment
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Setup mock .lisa environment
        os.makedirs(".lisa", exist_ok=True)
        self.state_file = ".lisa/state.json"
        
        # Create a mock state file
        initial_state = {"mode": "SPIKE", "task": "Testing"}
        with open(self.state_file, 'w') as f:
            json.dump(initial_state, f)
            
        # Create a dummy log file to test copying
        with open(".lisa/session.log", 'w') as f:
            f.write("Log content")
            
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('time.strftime')
    def test_archive_session_creates_timestamped_folder(self, mock_strftime):
        """Test that archive_session creates a folder with the current timestamp."""
        mock_timestamp = "20240101-120000"
        mock_strftime.return_value = mock_timestamp
        
        archive_path = archive_session(os.getcwd())
        
        expected_path = os.path.join(os.getcwd(), ".lisa", "archive", mock_timestamp)
        self.assertEqual(archive_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))
        
        # Verify copied files
        self.assertTrue(os.path.exists(os.path.join(expected_path, "state.json")))
        self.assertTrue(os.path.exists(os.path.join(expected_path, "session.log")))

    def test_archive_session_preserves_content(self):
        """Test that the archived content matches original."""
        archive_path = archive_session(os.getcwd())
        
        original_state = {"mode": "SPIKE", "task": "Testing"}
        
        with open(os.path.join(archive_path, "state.json"), 'r') as f:
            archived_state = json.load(f)
            
        self.assertEqual(archived_state, original_state)

    def test_reset_session_clears_state(self):
        """Test that reset_session clears state to defaults."""
        reset_session(os.getcwd())
        
        with open(self.state_file, 'r') as f:
            new_state = json.load(f)
            
        # Should adhere to StateManager defaults
        self.assertEqual(new_state.get("mode"), "NORMAL")
        self.assertEqual(new_state.get("status"), "IDLE")

    def test_archive_handles_missing_files_gracefully(self):
        """Test that archiver doesn't crash if .lisa is empty or missing expected files."""
        # Remove state file
        os.remove(self.state_file)
        
        try:
            archive_path = archive_session(os.getcwd())
            self.assertTrue(os.path.exists(archive_path))
        except Exception as e:
            self.fail(f"archive_session raised exception on missing file: {e}")

    @patch('shutil.copy2')
    @patch('sys.stderr')
    def test_archive_logs_warning_on_permission_error(self, mock_stderr, mock_copy):
        """Test that a PermissionError during copy logs a warning and continues."""
        mock_copy.side_effect = PermissionError("Access denied")
        
        archive_session(os.getcwd())
        
        # Verify that we didn't crash and logged a warning
        # Since we are mocking copy2, it will fail for files. copytree might still run for dirs.
        # We expect at least one warning call if files exist.
        self.assertTrue(mock_stderr.write.called, "Should have written to stderr on error")
        args, _ = mock_stderr.write.call_args
        self.assertIn("[WARNING]", args[0])

if __name__ == '__main__':
    unittest.main()
