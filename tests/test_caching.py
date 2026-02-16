
import unittest
import os
import json
import time
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Adjust path to import scripts
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.lisa.context_stats import update_cache, get_cached_health_icon, CACHE_FILE
from scripts.lisa.config import ConfigManager

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

    @patch('scripts.lisa.context_stats.scan_workspace')
    @patch('scripts.lisa.config.ConfigManager.load')
    def test_get_cached_health_icon_hit(self, mock_config_load, mock_scan):
        """Test that get_cached_health_icon returns cached value if valid."""
        # Setup config
        mock_config_load.return_value = {"context_limit": 10000, "context_check_interval": 600}
        
        # Setup cache
        params = {
            "token_count": 500,
            "health": "GREEN",
            "timestamp": time.time() # Fresh cache
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(params, f)
            
        icon = get_cached_health_icon()
        
        self.assertEqual(icon, "🟢")
        mock_scan.assert_not_called()

    @patch('scripts.lisa.context_stats.scan_workspace')
    @patch('scripts.lisa.config.ConfigManager.load')
    def test_get_cached_health_icon_miss_expired(self, mock_config_load, mock_scan):
        """Test that get_cached_health_icon re-scans if cache is expired."""
        # Setup config
        mock_config_load.return_value = {"context_limit": 10000, "context_check_interval": 600}
        
        # Setup EXPIRED cache (older than 600s)
        params = {
            "token_count": 500,
            "health": "GREEN",
            "timestamp": time.time() - 700 
        }
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(params, f)
            
        # Mock scan result to return high usage (RED)
        mock_scan.return_value = (9500, 50) 
        
        icon = get_cached_health_icon()
        
        self.assertEqual(icon, "🔴") # Should be RED now
        mock_scan.assert_called_once()
        
        # Verify cache was updated
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
        self.assertEqual(data["health"], "RED")
        self.assertGreater(data["timestamp"], params["timestamp"])

    @patch('scripts.lisa.context_stats.scan_workspace')
    def test_get_cached_health_icon_no_cache(self, mock_scan):
        """Test behavior when no cache exists."""
        mock_scan.return_value = (100, 5)
        
        icon = get_cached_health_icon()
        
        self.assertEqual(icon, "🟢")
        mock_scan.assert_called_once()

if __name__ == '__main__':
    unittest.main()
