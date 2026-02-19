
import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Adjust path to import scripts
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from lisa.context_stats import update_cache, get_cached_health_icon, CACHE_FILE
from lisa.config import ConfigManager

class TestContextCaching(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for cache file
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Ensure .lisa directory exists in temp dir
        os.makedirs(".lisa", exist_ok=True)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_update_cache_creates_file(self):
        """Test that update_cache creates the cache file with correct data."""
        token_count = 1500
        health = "GREEN"
        
        update_cache(token_count, health)
        
        self.assertTrue(os.path.exists(CACHE_FILE))
        
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data["token_count"], token_count)
        self.assertEqual(data["health"], health)
        self.assertIn("timestamp", data)
        self.assertIsInstance(data["timestamp"], float)

    @patch('lisa.config.ConfigManager.load')
    def test_get_cached_health_icon_green_turns(self, mock_config_load):
        """Test that get_cached_health_icon returns green when turn count is low."""
        mock_config_load.return_value = {
            "turn_warning_threshold": 12, "turn_limit": 20
        }

        # Write state with low turn count
        state_path = os.path.join(self.test_dir, ".lisa", "lisa_storage.json")
        with open(state_path, "w") as f:
            json.dump({"turn_count": 3}, f)

        icon = get_cached_health_icon()
        self.assertEqual(icon, "🟢")

    @patch('lisa.config.ConfigManager.load')
    def test_get_cached_health_icon_amber_turns(self, mock_config_load):
        """Test that get_cached_health_icon returns amber at warning threshold."""
        mock_config_load.return_value = {
            "turn_warning_threshold": 12, "turn_limit": 20
        }

        state_path = os.path.join(self.test_dir, ".lisa", "lisa_storage.json")
        with open(state_path, "w") as f:
            json.dump({"turn_count": 14}, f)

        icon = get_cached_health_icon()
        self.assertEqual(icon, "🟡")

    @patch('lisa.config.ConfigManager.load')
    def test_get_cached_health_icon_red_turns(self, mock_config_load):
        """Test that get_cached_health_icon returns red when turns exceed limit."""
        mock_config_load.return_value = {
            "turn_warning_threshold": 12, "turn_limit": 20
        }

        state_path = os.path.join(self.test_dir, ".lisa", "lisa_storage.json")
        with open(state_path, "w") as f:
            json.dump({"turn_count": 25}, f)

        icon = get_cached_health_icon()
        self.assertEqual(icon, "🔴")

    def test_get_cached_health_icon_no_state(self):
        """Test that get_cached_health_icon returns green when no state exists (turn 0)."""
        icon = get_cached_health_icon()
        self.assertEqual(icon, "🟢")

if __name__ == '__main__':
    unittest.main()
