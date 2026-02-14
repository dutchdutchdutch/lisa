import os
import json
import unittest
import tempfile
import shutil
import sys

# Add scripts to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

from lisa.config import ConfigManager

class TestConfigLoading(unittest.TestCase):
    def setUp(self):
        # Create temp directories for configs
        self.test_dir = tempfile.mkdtemp()
        self.user_config_path = os.path.join(self.test_dir, "user_config.json")
        self.project_config_path = os.path.join(self.test_dir, "project_config.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_defaults_only(self):
        """Test loading with no config files."""
        manager = ConfigManager(
            user_config_path=self.user_config_path,
            project_config_path=self.project_config_path
        )
        self.assertEqual(manager.get("strictness"), "strict")
        self.assertTrue(manager.get("spike_mode_allowed"))

    def test_user_override(self):
        """Test user config overriding defaults."""
        user_data = {"strictness": "lenient", "user_key": "user_value"}
        with open(self.user_config_path, "w") as f:
            json.dump(user_data, f)
            
        manager = ConfigManager(
            user_config_path=self.user_config_path,
            project_config_path=self.project_config_path
        )
        self.assertEqual(manager.get("strictness"), "lenient")
        self.assertEqual(manager.get("user_key"), "user_value")

    def test_project_override(self):
        """Test project config overriding user and defaults."""
        user_data = {"strictness": "lenient", "common_key": "user"}
        with open(self.user_config_path, "w") as f:
            json.dump(user_data, f)
            
        project_data = {"strictness": "super_strict", "common_key": "project"}
        with open(self.project_config_path, "w") as f:
            json.dump(project_data, f)
            
        manager = ConfigManager(
            user_config_path=self.user_config_path,
            project_config_path=self.project_config_path
        )
        self.assertEqual(manager.get("strictness"), "super_strict")
        self.assertEqual(manager.get("common_key"), "project")

    def test_corrupt_file_resilience(self):
        """Test handling of corrupt config files with warning."""
        with open(self.user_config_path, "w") as f:
            f.write("INVALID JSON")
            
        # Capture stderr
        from io import StringIO
        import sys
        
        captured_stderr = StringIO()
        original_stderr = sys.stderr
        try:
            sys.stderr = captured_stderr
            manager = ConfigManager(
                user_config_path=self.user_config_path,
                project_config_path=self.project_config_path
            )
        finally:
            sys.stderr = original_stderr
            
        # Should fall back to defaults effectively ignoring corrupt file
        self.assertEqual(manager.get("strictness"), "strict")
        
        # Verify warning was printed
        self.assertIn("[LISA] [WARNING]", captured_stderr.getvalue())
        self.assertIn("Failed to load config", captured_stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
