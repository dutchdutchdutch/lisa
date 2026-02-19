import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from lisa.commands import context_status, context_size, context_health, workspace_size
from lisa.state import ContextActivity

class TestContextCommands(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.StateManager')
    def test_context_status(self, MockStateManager):
        """Should verify context status output."""
        # Mock State
        mock_instance = MockStateManager.return_value
        mock_instance.load.return_value = {"activity": ContextActivity.MONITORING}
        
        with patch('lisa.commands.print_with_status') as mock_print:
            ret_code = context_status([])
            self.assertEqual(ret_code, 0)
            mock_print.assert_any_call("Current Activity: Monitoring", status_icon="ℹ️")

    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_context_size(self, mock_find_root, mock_scan):
        """Should verify context size metrics."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (500, 10) # 500 tokens, 10 files
        
        with patch('lisa.commands.print_with_status') as mock_print:
            ret_code = context_size([])
            self.assertEqual(ret_code, 0)
            mock_print.assert_any_call("Token Count: 500", status_icon="📊")
            mock_print.assert_any_call("File Count:  10", status_icon="📂")


    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_context_health(self, mock_find_root, mock_scan, MockConfig):
        """Should verify context health report leads with turn-based health."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (128000, 20) # 80% saturation

        # Mock Config
        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        with patch('lisa.commands.print_with_status') as mock_print:
            ret_code = context_health([])
            self.assertEqual(ret_code, 0)
            # AC3: Turn-based health appears first (primary signal)
            mock_print.assert_any_call("Context Pressure (Turns)", status_icon="🟢")
            # AC3: Workspace size appears second (supplementary)
            mock_print.assert_any_call("Workspace Size (Files on Disk)", status_icon="📂")
            # Workspace saturation still present
            mock_print.assert_any_call("Saturation:      80% (128000 / 160000 tokens)", status_icon="📈")

    @patch('lisa.commands.get_cache_status')
    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_check_context_output(self, mock_find_root, mock_scan, MockConfig, mock_cache_status):
        """Should verify check_context leads with turns and includes disclaimer."""
        from lisa.commands import check_context  # Import here to avoid early import issues

        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 50)

        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        # Ensure cache is stale or empty so it triggers a scan
        mock_cache_status.return_value = {}

        with patch('builtins.print') as mock_print:
            with patch('lisa.commands.print_with_status') as mock_status:
                ret_code = check_context([])
                self.assertEqual(ret_code, 0)

                # AC: Turn-based health appears first
                mock_status.assert_any_call("Context Pressure (Turns)")
                # AC: Workspace size appears second
                mock_status.assert_any_call("Workspace Size (On-Disk)")
                # Check for disclaimer in standard print
                mock_print.assert_any_call("    Approximation method across models for watchdog purposes. Not billing grade accurate.")

    # --- Story 7.10: Workspace Size Awareness ---

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_workspace_size_output(self, mock_find_root, mock_scan, MockConfig):
        """AC1: Should display workspace token count, file count, and usage percentage."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 50)

        mock_config = {"context_limit": 160000}
        MockConfig.return_value.load.return_value = mock_config

        with patch('builtins.print') as mock_raw_print:
            with patch('lisa.commands.print_with_status') as mock_print:
                ret_code = workspace_size([])
                self.assertEqual(ret_code, 0)
                # AC1: Labeled as "Workspace Size"
                mock_print.assert_any_call("Workspace Size (On-Disk)")
                # AC1: Token count with limit
                mock_print.assert_any_call("Token Count: 5000 / 160000", status_icon="📊")
                # AC1: File count
                mock_print.assert_any_call("File Count:  50", status_icon="📂")
                # AC1: Usage percentage
                mock_print.assert_any_call("Usage:       3.1%", status_icon="🟢")
                # Disclaimer present
                mock_raw_print.assert_any_call("    Approximation method across models for watchdog purposes. Not billing grade accurate.")

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_workspace_size_amber(self, mock_find_root, mock_scan, MockConfig):
        """AC1: Should show amber icon when usage is 70-90%."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (120000, 100)

        mock_config = {"context_limit": 160000}
        MockConfig.return_value.load.return_value = mock_config

        with patch('builtins.print'):
            with patch('lisa.commands.print_with_status') as mock_print:
                ret_code = workspace_size([])
                self.assertEqual(ret_code, 0)
                mock_print.assert_any_call("Usage:       75.0%", status_icon="🟡")

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_workspace_size_red(self, mock_find_root, mock_scan, MockConfig):
        """AC1: Should show red icon when usage exceeds 90%."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (150000, 200)

        mock_config = {"context_limit": 160000}
        MockConfig.return_value.load.return_value = mock_config

        with patch('builtins.print'):
            with patch('lisa.commands.print_with_status') as mock_print:
                ret_code = workspace_size([])
                self.assertEqual(ret_code, 0)
                mock_print.assert_any_call("Usage:       93.8%", status_icon="🔴")

    @patch('lisa.commands.find_project_root')
    def test_workspace_size_no_project_root(self, mock_find_root):
        """Should return 1 when no project root found."""
        mock_find_root.side_effect = FileNotFoundError("No project root")

        with patch('lisa.commands.print_with_status') as mock_print:
            ret_code = workspace_size([])
            self.assertEqual(ret_code, 1)
            mock_print.assert_any_call("Error: Could not determine project root.", status_icon="🔴")

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_workspace_size_uses_context_limit(self, mock_find_root, mock_scan, MockConfig):
        """AC4: Should use context_limit from config as workspace token budget."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (50000, 30)

        mock_config = {"context_limit": 100000}
        MockConfig.return_value.load.return_value = mock_config

        with patch('builtins.print'):
            with patch('lisa.commands.print_with_status') as mock_print:
                ret_code = workspace_size([])
                self.assertEqual(ret_code, 0)
                # Uses custom context_limit as budget
                mock_print.assert_any_call("Token Count: 50000 / 100000", status_icon="📊")
                mock_print.assert_any_call("Usage:       50.0%", status_icon="🟢")

    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_context_size_backward_compat(self, mock_find_root, mock_scan):
        """AC3: context_size still works and shows workspace (on-disk) label."""
        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (500, 10)

        with patch('lisa.commands.print_with_status') as mock_print:
            ret_code = context_size([])
            self.assertEqual(ret_code, 0)
            # AC3: Output clarifies these are workspace metrics
            mock_print.assert_any_call("Workspace Metrics (On-Disk)")


if __name__ == "__main__":
    unittest.main()
