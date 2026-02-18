"""Tests for the LISA lifecycle hooks engine."""
import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, call


from lisa.hooks import LIFECYCLE_EVENTS, run_hooks, run_story_complete


class TestLifecycleEvents(unittest.TestCase):
    """Tests for LIFECYCLE_EVENTS constant."""

    def test_all_events_defined(self):
        """All five lifecycle events should be defined."""
        expected = {"story-kickoff", "story-in-dev", "story-test", "story-complete", "context-reset"}
        self.assertEqual(set(LIFECYCLE_EVENTS), expected)


class TestRunHooks(unittest.TestCase):
    """Tests for the run_hooks function."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(self.lisa_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('lisa.hooks.subprocess.run')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_runs_configured_hooks(self, mock_print, mock_config_cls, mock_subprocess):
        """Should execute each command configured for the event."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "lifecycle_hooks": {
                "story-in-dev": ["lisa turns"],
            },
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        results = run_hooks("story-in-dev", self.test_dir)

        self.assertEqual(len(results), 1)
        cmd, success, output = results[0]
        self.assertEqual(cmd, "lisa turns")
        self.assertTrue(success)

    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_empty_hooks_noop(self, mock_print, mock_config_cls):
        """Empty hook list should return empty results without errors."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "lifecycle_hooks": {"story-kickoff": []},
        }.get(key, default)
        mock_config_cls.return_value = mock_config

        results = run_hooks("story-kickoff", self.test_dir)

        self.assertEqual(results, [])

    @patch('lisa.hooks.subprocess.run')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_failed_hook_logs_warning(self, mock_print, mock_config_cls, mock_subprocess):
        """Failed hook should log warning but not raise (fail-open, AC3)."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "lifecycle_hooks": {"context-reset": ["lisa checkpoint"]},
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_subprocess.side_effect = Exception("command not found")

        results = run_hooks("context-reset", self.test_dir)

        self.assertEqual(len(results), 1)
        cmd, success, output = results[0]
        self.assertFalse(success)
        # Should have logged a warning
        warning_calls = [c for c in mock_print.call_args_list if "WARNING" in str(c)]
        self.assertTrue(len(warning_calls) > 0, "Expected a warning to be logged")

    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_unknown_event_returns_empty(self, mock_print, mock_config_cls):
        """Unknown event name should return empty results (not crash)."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "lifecycle_hooks": {},
        }.get(key, default)
        mock_config_cls.return_value = mock_config

        results = run_hooks("nonexistent-event", self.test_dir)

        self.assertEqual(results, [])

    @patch('lisa.hooks.subprocess.run')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_multiple_hooks_all_run(self, mock_print, mock_config_cls, mock_subprocess):
        """Multiple hooks for an event should all be executed."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "lifecycle_hooks": {"story-complete": ["lisa polish", "lisa context"]},
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        results = run_hooks("story-complete", self.test_dir)

        self.assertEqual(len(results), 2)
        self.assertTrue(all(s for _, s, _ in results))

    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_missing_config_key_noop(self, mock_print, mock_config_cls):
        """Missing lifecycle_hooks config should return empty results."""
        mock_config = MagicMock()
        mock_config.get.return_value = None
        mock_config_cls.return_value = mock_config

        results = run_hooks("story-kickoff", self.test_dir)

        self.assertEqual(results, [])


class TestRunStoryComplete(unittest.TestCase):
    """Tests for the run_story_complete orchestration function."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(self.lisa_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('lisa.hooks.run_hooks')
    @patch('lisa.commands.check_context')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_orchestration_runs_hooks_then_health(self, mock_print, mock_config_cls, mock_check, mock_run_hooks):
        """story-complete should run hooks, then health check."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "hooks_mode": "auto",
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_run_hooks.return_value = []
        mock_check.return_value = 0  # GREEN

        result = run_story_complete(self.test_dir)

        self.assertEqual(result, 0)
        mock_run_hooks.assert_called_once_with("story-complete", self.test_dir)
        mock_check.assert_called_once()

    @patch('lisa.hooks.run_hooks')
    @patch('lisa.commands.check_context')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_orchestration_remediation_on_amber(self, mock_print, mock_config_cls, mock_check, mock_run_hooks):
        """Should trigger remediation when health check returns AMBER (exit code 2)."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "hooks_mode": "auto",
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_run_hooks.return_value = []
        mock_check.return_value = 2  # AMBER

        result = run_story_complete(self.test_dir)

        # Should still succeed (fail-open) but log remediation
        self.assertEqual(result, 0)
        # Verify remediation was mentioned
        remediation_calls = [c for c in mock_print.call_args_list if "remediation" in str(c).lower() or "curator" in str(c).lower() or "checkpoint" in str(c).lower()]
        self.assertTrue(len(remediation_calls) > 0, "Expected remediation output")

    @patch('lisa.hooks.run_hooks')
    @patch('lisa.commands.check_context')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_orchestration_interactive_mode(self, mock_print, mock_config_cls, mock_check, mock_run_hooks):
        """Interactive mode should present findings instead of auto-remediating."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "hooks_mode": "interactive",
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_run_hooks.return_value = []
        mock_check.return_value = 2  # AMBER

        result = run_story_complete(self.test_dir)

        self.assertEqual(result, 0)
        # Should mention interactive/prompt
        interactive_calls = [c for c in mock_print.call_args_list if "interactive" in str(c).lower() or "recommend" in str(c).lower() or "manual" in str(c).lower()]
        self.assertTrue(len(interactive_calls) > 0, "Expected interactive mode output")

    @patch('lisa.hooks.run_hooks')
    @patch('lisa.commands.check_context')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_orchestration_green_no_remediation(self, mock_print, mock_config_cls, mock_check, mock_run_hooks):
        """GREEN health check should not trigger remediation."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "hooks_mode": "auto",
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_run_hooks.return_value = []
        mock_check.return_value = 0  # GREEN

        result = run_story_complete(self.test_dir)

        self.assertEqual(result, 0)
        # Should NOT mention remediation
        remediation_calls = [c for c in mock_print.call_args_list if "remediation" in str(c).lower()]
        self.assertEqual(len(remediation_calls), 0, "No remediation expected for GREEN")

    @patch('lisa.hooks.run_hooks')
    @patch('lisa.commands.check_context')
    @patch('lisa.hooks.ConfigManager')
    @patch('lisa.hooks.print_with_status')
    def test_orchestration_failopen_on_error(self, mock_print, mock_config_cls, mock_check, mock_run_hooks):
        """Orchestration should not crash even if check_context raises."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "hooks_mode": "auto",
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        mock_run_hooks.return_value = []
        mock_check.side_effect = Exception("scan failed")

        result = run_story_complete(self.test_dir)

        self.assertEqual(result, 0)  # fail-open


if __name__ == "__main__":
    unittest.main()
