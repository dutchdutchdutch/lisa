import unittest
import os
import time
import tempfile
import shutil
from unittest.mock import patch
from scripts.lisa.commands import checkpoint, init_session

class TestCheckpoint(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True) # Marker for project root
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
        
    def test_checkpoint_missing_file(self):
        """Should fail if external state file does not exist."""
        # Ensure file is absent
        if os.path.exists("todo.md"):
            os.remove("todo.md")
            
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            ret_code = checkpoint([])
            self.assertEqual(ret_code, 1)
            mock_print.assert_any_call("Error: 'todo.md' not found.", status_icon="🔴")

    def test_checkpoint_stale_file(self):
        """Should fail if file is older than threshold (default 600s)."""
        with open("todo.md", "w") as f:
            f.write("# Old Todo")
            
        old_time = time.time() - (15 * 60) # 15 mins ago
        os.utime("todo.md", (old_time, old_time))
        
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            ret_code = checkpoint([])
            self.assertEqual(ret_code, 1)

    def test_checkpoint_fresh_file(self):
        """Should pass if file is fresh."""
        with open("todo.md", "w") as f:
            f.write("# Fresh Todo")
            
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            ret_code = checkpoint([])
            self.assertEqual(ret_code, 0)
            mock_print.assert_any_call("Checkpoint Verified (todo.md).", status_icon="🟢")

    def test_init_session_prints_content(self):
        """lisa init should print file content."""
        content = "# My Context\n- [ ] Task 1"
        with open("todo.md", "w") as f:
            f.write(content)
            
        with patch('builtins.print') as mock_print:
            with patch('scripts.lisa.commands.print_with_status') as mock_status:
                ret_code = init_session([])
                self.assertEqual(ret_code, 0)
                mock_print.assert_any_call(content)
                mock_status.assert_any_call("Context Injected.", status_icon="🟢")

    def test_config_overrides(self):
        """Should respect custom filename and ttl from config."""
        # Create custom file
        custom_file = "status.md"
        with open(custom_file, "w") as f:
            f.write("# Custom Status")
            
        # Mock ConfigManager to return custom values
        mock_config = {
            "external_state_file": custom_file,
            "external_state_ttl": 60
        }
        
        with patch('scripts.lisa.commands.ConfigManager') as MockConfig:
             MockConfig.return_value.load.return_value = mock_config
             MockConfig.return_value.get.side_effect = mock_config.get
             
             with patch('scripts.lisa.commands.print_with_status') as mock_print:
                 # Should pass because file exists and is fresh
                 ret_code = checkpoint([])
                 self.assertEqual(ret_code, 0)
                 mock_print.assert_any_call(f"Checkpoint Verified ({custom_file}).", status_icon="🟢")

if __name__ == "__main__":
    unittest.main()
