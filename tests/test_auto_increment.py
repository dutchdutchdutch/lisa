import unittest
import os
import shutil
import tempfile
import json
import time
from unittest.mock import patch, MagicMock
from lisa.state import StateManager
from lisa.commands import turns, check_context


class TestAutoIncrementTurn(unittest.TestCase):
    """Story 5.9: Auto-increment turn counter on every response cycle."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_auto_increment_increments_turn(self):
        """AC1: When any LISA command runs, the turn count reflects response cycles (not 0)."""
        manager = StateManager(project_root=self.test_dir)
        state = manager.load()
        self.assertEqual(state.get("turn_count", 0), 0)

        # Auto-increment should bump the turn count
        result = manager.auto_increment_turn()
        self.assertTrue(result)  # Should indicate increment happened

        state = manager.load()
        self.assertEqual(state["turn_count"], 1)

    def test_auto_increment_deduplicates_within_same_second(self):
        """AC2: Multiple LISA commands in a single response increment only once."""
        manager = StateManager(project_root=self.test_dir)

        # First call should increment
        result1 = manager.auto_increment_turn()
        self.assertTrue(result1)

        # Second call within same second should NOT increment
        result2 = manager.auto_increment_turn()
        self.assertFalse(result2)

        state = manager.load()
        self.assertEqual(state["turn_count"], 1)

    def test_auto_increment_increments_on_new_second(self):
        """Auto-increment fires again when epoch second changes."""
        manager = StateManager(project_root=self.test_dir)

        # First call increments
        manager.auto_increment_turn()
        state = manager.load()
        self.assertEqual(state["turn_count"], 1)

        # Simulate time advancing by 1 second
        state = manager.load()
        state["last_auto_increment_ts"] = int(time.time()) - 2
        manager.save(state)

        # Second call should now increment (different second)
        result = manager.auto_increment_turn()
        self.assertTrue(result)

        state = manager.load()
        self.assertEqual(state["turn_count"], 2)

    def test_explicit_turns_overrides_auto_increment(self):
        """AC3: Explicit `lisa turns <N>` overrides auto-tracked value."""
        manager = StateManager(project_root=self.test_dir)

        # Auto-increment a few times
        manager.auto_increment_turn()
        # Simulate new second
        state = manager.load()
        state["last_auto_increment_ts"] = int(time.time()) - 2
        manager.save(state)
        manager.auto_increment_turn()

        state = manager.load()
        self.assertEqual(state["turn_count"], 2)

        # Explicit set overrides
        manager.update("turn_count", 50)
        state = manager.load()
        self.assertEqual(state["turn_count"], 50)

    def test_reset_clears_auto_increment_marker(self):
        """AC5: lisa reset clears the auto-increment counter and cycle marker."""
        manager = StateManager(project_root=self.test_dir)

        # Auto-increment
        manager.auto_increment_turn()
        state = manager.load()
        self.assertIn("last_auto_increment_ts", state)
        self.assertEqual(state["turn_count"], 1)

        # Reset
        manager.reset_turn()
        state = manager.load()
        self.assertEqual(state["turn_count"], 0)
        # Cycle marker should also be cleared so next command increments
        self.assertNotIn("last_auto_increment_ts", state)

    def test_auto_increment_stores_cycle_marker(self):
        """Deduplication: auto_increment stores a timestamp marker in state."""
        manager = StateManager(project_root=self.test_dir)
        manager.auto_increment_turn()

        state = manager.load()
        self.assertIn("last_auto_increment_ts", state)
        self.assertIsInstance(state["last_auto_increment_ts"], int)


class TestAutoIncrementIntegration(unittest.TestCase):
    """Integration: auto-increment fires from the CLI entry point."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.find_project_root')
    def test_turns_report_shows_auto_incremented_value(self, mock_root):
        """AC1: Turn count reflects response cycles even without explicit set."""
        mock_root.return_value = self.test_dir

        # Simulate auto-increment (as __main__ would do)
        manager = StateManager(project_root=self.test_dir)
        manager.auto_increment_turn()

        # Now `lisa turns` (report mode) should show 1, not 0
        with patch('lisa.commands.print_with_status') as mock_print:
            result = turns([])
            self.assertEqual(result, 0)
            mock_print.assert_called_with("Current Turn: 1", status_icon="⏱️")

    @patch('lisa.commands.find_project_root')
    def test_explicit_set_after_auto_increment(self, mock_root):
        """AC3: Explicit value takes precedence after auto-increment."""
        mock_root.return_value = self.test_dir

        # Auto-increment first
        manager = StateManager(project_root=self.test_dir)
        manager.auto_increment_turn()

        # Explicit set to 7
        with patch('lisa.commands.print_with_status'):
            result = turns(["7"])
            self.assertEqual(result, 0)

        # Verify the explicit value stuck
        state = manager.load()
        self.assertEqual(state["turn_count"], 7)


class TestAutoIncrementThresholds(unittest.TestCase):
    """AC4: Auto-tracked turns trigger Goldfish Threshold warnings."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.ConfigManager')
    def test_auto_increment_triggers_amber_at_goldfish(self, MockConfig, mock_root, mock_scan):
        """AC4: Auto-tracked turn crossing 12 fires amber warning."""
        mock_root.return_value = self.test_dir
        mock_scan.return_value = (500, 5)
        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = lambda k, d=None: mock_config.get(k, d)

        # Simulate 12 auto-increments (at Goldfish Threshold)
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 12)

        with patch('lisa.commands.print_with_status') as mock_print:
            check_context([])
            mock_print.assert_any_call("Current Turn: 12", status_icon="🟡")
            mock_print.assert_any_call("Status: AMBER", status_icon="🟡")


class TestMainAutoIncrement(unittest.TestCase):
    """Verify __main__.py calls auto_increment_turn before dispatch."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(".lisa", exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('lisa.__main__.find_project_root')
    @patch('lisa.__main__.StateManager')
    @patch('lisa.__main__.enable_spike', return_value=0)
    def test_main_calls_auto_increment(self, _mock_spike, MockStateManager, mock_root):
        """main() calls auto_increment_turn before dispatching commands."""
        from lisa.__main__ import main

        mock_root.return_value = self.test_dir
        mock_manager = MagicMock()
        MockStateManager.return_value = mock_manager

        with patch('sys.argv', ['lisa', 'spike']):
            try:
                main()
            except SystemExit:
                pass

        mock_manager.auto_increment_turn.assert_called_once()


if __name__ == '__main__':
    unittest.main()
