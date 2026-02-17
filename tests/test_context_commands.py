import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from scripts.lisa.commands import context_status, context_size, context_health
from scripts.lisa.state import ContextActivity

class TestContextCommands(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('scripts.lisa.commands.StateManager')
    def test_context_status(self, MockStateManager):
        """Should verify context status output."""
        # Mock State
        mock_instance = MockStateManager.return_value
        mock_instance.load.return_value = {"activity": ContextActivity.MONITORING}
        
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            ret_code = context_status([])
            self.assertEqual(ret_code, 0)
            mock_print.assert_any_call("Current Activity: Monitoring", status_icon="ℹ️")

    @patch('scripts.lisa.commands.scan_workspace')
    @patch('scripts.lisa.commands.find_project_root')
    def test_context_size(self, mock_find_root, mock_scan):
        """Should verify context size metrics."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (500, 10) # 500 tokens, 10 files
        
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            ret_code = context_size([])
            self.assertEqual(ret_code, 0)
            mock_print.assert_any_call("Token Count: 500", status_icon="📊")
            mock_print.assert_any_call("File Count:  10", status_icon="📂")


    @patch('scripts.lisa.commands.ConfigManager')
    @patch('scripts.lisa.commands.scan_workspace')
    @patch('scripts.lisa.commands.find_project_root')
    def test_context_health(self, mock_find_root, mock_scan, MockConfig):
        """Should verify context health report."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (16000, 20) # 80% saturation
        
        # Mock Config
        mock_config = {"context_limit": 20000}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get
        
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            # We mock DriftDetector implicitly via the module import inside the function
            # But simpler here is to let it run since it's deterministic
            ret_code = context_health([])
            self.assertEqual(ret_code, 0)
            # 16000 / 20000 = 80% -> WARNING (Saturation)
            # Saturation: 80% (16000 / 20000 tokens)
            mock_print.assert_any_call("Saturation:      80% (16000 / 20000 tokens)", status_icon="📈")
            mock_print.assert_any_call("Status:          WARNING (Saturation)", status_icon="rx")

    @patch('scripts.lisa.commands.get_cache_status')
    @patch('scripts.lisa.commands.ConfigManager')
    @patch('scripts.lisa.commands.scan_workspace')
    @patch('scripts.lisa.commands.find_project_root')
    def test_check_context_output(self, mock_find_root, mock_scan, MockConfig, mock_cache_status):
        """Should verify check_context output includes disclaimer."""
        from scripts.lisa.commands import check_context  # Import here to avoid early import issues 
        
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 50)
        
        mock_config = {"context_limit": 20000}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get
        
        # Ensure cache is stale or empty so it triggers a scan
        mock_cache_status.return_value = {}

        with patch('builtins.print') as mock_print:
            with patch('scripts.lisa.commands.print_with_status') as mock_status:
                ret_code = check_context([])
                self.assertEqual(ret_code, 0)
                
                # Check for disclaimer in standard print
                mock_print.assert_any_call("    Approximation method across models for watchdog purposes. Not billing grade accurate.")

if __name__ == "__main__":
    unittest.main()
