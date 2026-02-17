import unittest
from unittest.mock import patch, MagicMock
from scripts.lisa.commands import init_session
import os

class TestPermissionHandling(unittest.TestCase):
    
    @patch('scripts.lisa.commands.find_project_root')
    @patch('scripts.lisa.commands.ConfigManager')
    @patch('scripts.lisa.commands.print_with_status')
    def test_init_session_permission_error(self, mock_print_with_status, mock_config_manager, mock_find_root):
        # Setup mocks
        mock_find_root.return_value = "/mock/root"
        
        # Simulate PermissionError when loading config or accessing files
        mock_config_instance = mock_config_manager.return_value
        mock_config_instance.load.side_effect = PermissionError("Permission denied")
        
        # execution
        try:
            result = init_session([])
            
            # assertions
            self.assertEqual(result, 1)
            mock_print_with_status.assert_called_with("Error: Permission denied. Please check permissions on .lisa/ or the project root.", status_icon="🔴")
            
        except PermissionError:
            self.fail("init_session raised PermissionError instead of handling it gracefully")

    @patch('scripts.lisa.commands.find_project_root')
    @patch('scripts.lisa.commands.ConfigManager')
    @patch('builtins.open')
    @patch('scripts.lisa.commands.print_with_status')
    def test_init_session_file_read_permission_error(self, mock_print_with_status, mock_open, mock_config_manager, mock_find_root):
        # Setup mocks for successful config load but failed file read
        mock_find_root.return_value = "/mock/root"
        mock_config_instance = mock_config_manager.return_value
        mock_config_instance.load.return_value = mock_config_instance
        mock_config_instance.get.return_value = "todo.md"
        
        # Simulate PermissionError when opening todo.md
        mock_open.side_effect = PermissionError("Permission denied")
        
        # Check that file exists (to bypass the existence check)
        with patch('os.path.exists', return_value=True):
             result = init_session([])
        
        self.assertEqual(result, 1)
        # Verify we catch the specific exception
        # Note: The implementation uses `except Exception` which catches PermissionError too.
        # We want to verify it doesn't crash.
        # It should print the error.
        mock_print_with_status.assert_any_call("Error: Permission denied. Please check permissions on .lisa/ or the project root.", status_icon="🔴")
