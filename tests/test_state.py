import unittest
import os
import shutil
import tempfile
import json
from scripts.lisa.state import StateManager

class TestStateManager(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Create .lisa dir
        os.makedirs(".lisa", exist_ok=True)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_increment_turn(self):
        """Should increment turn_count in state file."""
        manager = StateManager(project_root=self.test_dir)
        
        # Initial State: 0 or undefined
        self.assertEqual(manager.load().get("turn_count", 0), 0)
        
        # Increment
        new_count = manager.increment_turn()
        self.assertEqual(new_count, 1)
        
        # Verify persistence
        with open(os.path.join(self.test_dir, ".lisa/state.json"), "r") as f:
            data = json.load(f)
            self.assertEqual(data["turn_count"], 1)

    def test_reset_turn(self):
        """Should reset turn_count to 0."""
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 15)
        
        manager.reset_turn()
        self.assertEqual(manager.load()["turn_count"], 0)
