import unittest
import os
import shutil
import tempfile
import json
from unittest.mock import patch, MagicMock
from scripts.lisa.state import StateManager
from scripts.lisa.commands import turns, check_context

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

    def test_turns_report_current(self):
        """Should report current turn count when called with no args."""
        # Set turn count to 5 first
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 5)
        
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = turns([])
            self.assertEqual(result, 0)
            mock_print.assert_called_with("Current Turn: 5", status_icon="⏱️")

    def test_turns_set_explicit(self):
        """Should set turn count to explicit value when given a number."""
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = turns(["7"])
            self.assertEqual(result, 0)
            mock_print.assert_called_with("Turn Counter Set: 7", status_icon="⏱️")
        
        # Verify it was persisted
        manager = StateManager(project_root=self.test_dir)
        state = manager.load()
        self.assertEqual(state.get("turn_count"), 7)

    def test_turns_invalid_input(self):
        """Should reject non-numeric input."""
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = turns(["abc"])
            self.assertEqual(result, 1)

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
