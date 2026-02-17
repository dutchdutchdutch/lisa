import unittest
import os
import shutil
import tempfile
import json
from unittest.mock import patch, MagicMock
from scripts.lisa.state import StateManager
from scripts.lisa.commands import tick, check_context

class TestTurnWatchdog(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Create .lisa dir
        os.makedirs(".lisa", exist_ok=True)
        # Mock project root to be test_dir
        self.patcher = patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir)
        self.patcher.start()
        
    def tearDown(self):
        self.patcher.stop()
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_tick_increments_turn(self):
        """Should increment turn count when tick is called."""
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            tick([])
            mock_print.assert_called_with("Turn Counter Incremented: 1", status_icon="⏱️")
            
            tick([])
            mock_print.assert_called_with("Turn Counter Incremented: 2", status_icon="⏱️")

    @patch('scripts.lisa.commands.scan_workspace')
    @patch('scripts.lisa.commands.ConfigManager')
    def test_check_context_display(self, MockConfig, mock_scan):
        """Should display turn count and correct status icon."""
        # Setup Mocks
        mock_scan.return_value = (500, 5) # Low tokens
        mock_config = {"context_limit": 20000}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get
        
        # Set turn count to 5 (GREEN)
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 5)
        
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            check_context([])
            mock_print.assert_any_call("Current Turn: 5", status_icon="🟢")
            mock_print.assert_any_call("Status: GREEN", status_icon="🟢")

    @patch('scripts.lisa.commands.scan_workspace')
    @patch('scripts.lisa.commands.ConfigManager')
    def test_check_context_traffic_light(self, MockConfig, mock_scan):
        """Should verify traffic light logic for turns (default & custom)."""
        mock_scan.return_value = (500, 5)
        
        # Test 1: Default Thresholds (12, 20)
        config_default = {"context_limit": 20000} # defaults used
        MockConfig.return_value.load.return_value = config_default
        MockConfig.return_value.get.side_effect = lambda k, d=None: config_default.get(k, d)
        
        manager = StateManager(project_root=self.test_dir)
        
        # AMBER Test (15 >= 12)
        manager.update("turn_count", 15)
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            check_context([])
            mock_print.assert_any_call("Current Turn: 15", status_icon="🟡")
            mock_print.assert_any_call("Status: AMBER", status_icon="🟡")
            mock_print.assert_any_call("WARNING: Approaching Turn Limit (12-20).", status_icon="🟡")

        # RED Test (25 > 20)
        manager.update("turn_count", 25)
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            check_context([])
            mock_print.assert_any_call("Current Turn: 25", status_icon="🔴")
            mock_print.assert_any_call("Status: RED", status_icon="🔴")
            mock_print.assert_any_call("CRITICAL: Turn Limit Exceeded (>20).", status_icon="🔴")

        # Test 2: Custom Thresholds (e.g. Warning 5, Limit 10)
        config_custom = {
            "context_limit": 20000, 
            "turn_warning_threshold": 5, 
            "turn_limit": 10
        }
        MockConfig.return_value.load.return_value = config_custom
        MockConfig.return_value.get.side_effect = lambda k, d=None: config_custom.get(k, d)
        
        # Verify Custom AMBER (6 >= 5)
        manager.update("turn_count", 6)
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            check_context([])
            mock_print.assert_any_call("Current Turn: 6", status_icon="🟡")
            mock_print.assert_any_call("WARNING: Approaching Turn Limit (5-10).", status_icon="🟡")
