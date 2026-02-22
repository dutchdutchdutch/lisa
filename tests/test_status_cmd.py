import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from lisa.commands import status_cmd, activate_cmd
from lisa.state import LISA_MODES, ContextActivity

class TestStatusCmd(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('lisa.commands.find_project_root')
    def test_status_inactive(self, mock_find_root):
        """Should report Inactive if no project root found."""
        mock_find_root.side_effect = FileNotFoundError("No project root")
        
        with patch('lisa.commands.print_with_status') as mock_print:
            status_cmd([])
            mock_print.assert_any_call("LISA is Inactive (Not a LISA project)", status_icon="⚪")

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.StateManager')
    def test_status_idle(self, MockStateManager, mock_find_root):
        """Should report Idle state."""
        mock_find_root.return_value = self.test_dir
        mock_instance = MockStateManager.return_value
        mock_instance.load.return_value = {
            "activity": ContextActivity.IDLE,
            "mode": LISA_MODES.NORMAL,
            "turn_count": 0
        }
        
        with patch('lisa.commands.print_with_status') as mock_print:
            status_cmd([])
            mock_print.assert_any_call("Activity: Idle / Ready", status_icon="📡")
            mock_print.assert_any_call("Mode:     NORMAL", status_icon="🛡️")

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.StateManager')
    def test_status_monitoring(self, MockStateManager, mock_find_root):
        """Should report Monitoring state."""
        mock_find_root.return_value = self.test_dir
        mock_instance = MockStateManager.return_value
        mock_instance.load.return_value = {
            "activity": ContextActivity.MONITORING,
            "mode": LISA_MODES.SPIKE,
            "turn_count": 5
        }
        
        with patch('lisa.commands.print_with_status') as mock_print:
            status_cmd([])
            mock_print.assert_any_call("Activity: Actively Monitoring", status_icon="📡")
            mock_print.assert_any_call("Mode:     SPIKE", status_icon="🛡️")
            mock_print.assert_any_call("Turn:     5", status_icon="🔢")

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.StateManager')
    def test_activate_success(self, MockStateManager, mock_find_root):
        """Should transition to monitoring on activate."""
        mock_find_root.return_value = self.test_dir
        mock_instance = MockStateManager.return_value
        
        with patch('lisa.commands.print_with_status') as mock_print:
            activate_cmd([])
            mock_instance.update.assert_called_with("activity", ContextActivity.MONITORING)
            mock_print.assert_any_call("LISA Activated", status_icon="🚀")

if __name__ == "__main__":
    unittest.main()
