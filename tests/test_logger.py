
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Adjust path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from lisa.logger import print_with_status

class TestLogger(unittest.TestCase):
    @patch('lisa.logger.get_current_icon')
    @patch('builtins.print')
    def test_print_with_status_fetches_icon(self, mock_print, mock_get_icon):
        """Test that print_with_status calls get_current_icon if icon is None."""
        mock_get_icon.return_value = "🔴"
        
        print_with_status("Test Message")
        
        mock_get_icon.assert_called_once()
        mock_print.assert_called_with("[🔴] Test Message")

    @patch('lisa.logger.get_current_icon')
    @patch('builtins.print')
    def test_print_with_status_uses_provided_icon(self, mock_print, mock_get_icon):
        """Test that print_with_status uses provided icon and skips fetch."""
        print_with_status("Test Message", status_icon="🟡")
        
        mock_get_icon.assert_not_called()
        mock_print.assert_called_with("[🟡] Test Message")

if __name__ == '__main__':
    unittest.main()
