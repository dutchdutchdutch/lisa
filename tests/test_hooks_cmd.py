"""Tests for the lisa hooks CLI command."""
import unittest
from unittest.mock import patch, MagicMock


from lisa.commands import run_hooks_cmd


class TestRunHooksCmd(unittest.TestCase):
    """Tests for the run_hooks_cmd CLI command."""

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.print_with_status')
    def test_no_args_shows_usage(self, mock_print, mock_root):
        """Should show usage when no event name provided."""
        result = run_hooks_cmd([])
        self.assertEqual(result, 1)
        mock_print.assert_any_call(
            "Usage: lisa hooks <event>",
            status_icon="🔴"
        )

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.print_with_status')
    def test_invalid_event_rejected(self, mock_print, mock_root):
        """Should reject unknown event names."""
        mock_root.return_value = "/tmp/test"
        result = run_hooks_cmd(["bad-event"])
        self.assertEqual(result, 1)

    @patch('lisa.commands.run_hooks')
    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.print_with_status')
    def test_valid_event_runs_hooks(self, mock_print, mock_root, mock_run_hooks):
        """Should call run_hooks for valid event name."""
        mock_root.return_value = "/tmp/test"
        mock_run_hooks.return_value = [("lisa turns", True, "ok")]
        result = run_hooks_cmd(["story-in-dev"])
        self.assertEqual(result, 0)
        mock_run_hooks.assert_called_once_with("story-in-dev", "/tmp/test")

    @patch('lisa.commands.run_story_complete')
    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.print_with_status')
    def test_story_complete_uses_orchestrator(self, mock_print, mock_root, mock_complete):
        """story-complete event should use the orchestrator function."""
        mock_root.return_value = "/tmp/test"
        mock_complete.return_value = 0
        result = run_hooks_cmd(["story-complete"])
        self.assertEqual(result, 0)
        mock_complete.assert_called_once_with("/tmp/test")

    @patch('lisa.commands.find_project_root', side_effect=FileNotFoundError)
    @patch('lisa.commands.print_with_status')
    def test_no_project_root(self, mock_print, mock_root):
        """Should return error when no project root found."""
        result = run_hooks_cmd(["story-kickoff"])
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
