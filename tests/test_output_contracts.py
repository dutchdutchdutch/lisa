"""Output Contract Tests — verifies each report command includes ALL expected fields.

These tests act as schema guards: if a field is removed or renamed,
the test fails immediately. This prevents regressions like the turn count
disappearing from `lisa context health` without being caught.
"""
import unittest
import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock, call

from lisa.commands import (
    context_status, context_size, context_health, polish, refactor
)
from lisa.state import ContextActivity


class TestContextHealthOutputContract(unittest.TestCase):
    """Every field in the context health report must be present."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        # Write a state file with a known turn count
        state_path = os.path.join(self.test_dir, ".lisa", "state.json")
        with open(state_path, "w") as f:
            json.dump({"turn_count": 5}, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_health_report_includes_all_fields(self, mock_root, mock_scan, MockConfig):
        """context_health output must include: Saturation, Signal Ratio, Status, Turn Count."""
        mock_root.return_value = self.test_dir
        mock_scan.return_value = (10000, 20)

        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        with patch('lisa.commands.print_with_status') as mock_print:
            result = context_health([])

        self.assertEqual(result, 0)

        # Collect all printed field labels
        all_output = " ".join(str(c) for c in mock_print.call_args_list)

        required_fields = [
            "Context Health Report",
            "Saturation:",
            "Signal Ratio:",
            "Status:",
            "Turn Count:",
        ]
        for field in required_fields:
            self.assertIn(field, all_output, f"Missing required field: '{field}'")

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_health_turn_count_color_green(self, mock_root, mock_scan, MockConfig):
        """Turn count below warning threshold should use green icon."""
        mock_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 10)
        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        with patch('lisa.commands.print_with_status') as mock_print:
            context_health([])

        # Find the Turn Count call specifically
        turn_calls = [c for c in mock_print.call_args_list if "Turn Count:" in str(c)]
        self.assertEqual(len(turn_calls), 1, "Expected exactly one Turn Count field")
        self.assertIn("🟢", str(turn_calls[0]))

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_health_turn_count_color_amber(self, mock_root, mock_scan, MockConfig):
        """Turn count at warning threshold should use amber icon."""
        # Write state with turn count at threshold
        state_path = os.path.join(self.test_dir, ".lisa", "state.json")
        with open(state_path, "w") as f:
            json.dump({"turn_count": 12}, f)

        mock_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 10)
        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        with patch('lisa.commands.print_with_status') as mock_print:
            context_health([])

        turn_calls = [c for c in mock_print.call_args_list if "Turn Count:" in str(c)]
        self.assertIn("🟡", str(turn_calls[0]))

    @patch('lisa.commands.ConfigManager')
    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_health_turn_count_color_red(self, mock_root, mock_scan, MockConfig):
        """Turn count above turn limit should use red icon."""
        state_path = os.path.join(self.test_dir, ".lisa", "state.json")
        with open(state_path, "w") as f:
            json.dump({"turn_count": 25}, f)

        mock_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 10)
        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        with patch('lisa.commands.print_with_status') as mock_print:
            context_health([])

        turn_calls = [c for c in mock_print.call_args_list if "Turn Count:" in str(c)]
        self.assertIn("🔴", str(turn_calls[0]))


class TestContextSizeOutputContract(unittest.TestCase):
    """Every field in the context size report must be present."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        state_path = os.path.join(self.test_dir, ".lisa", "state.json")
        with open(state_path, "w") as f:
            json.dump({"turn_count": 3}, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.scan_workspace')
    @patch('lisa.commands.find_project_root')
    def test_size_report_includes_all_fields(self, mock_root, mock_scan):
        """context_size output must include: Token Count, File Count, Turn Count."""
        mock_root.return_value = self.test_dir
        mock_scan.return_value = (8000, 42)

        with patch('lisa.commands.print_with_status') as mock_print:
            result = context_size([])

        self.assertEqual(result, 0)

        all_output = " ".join(str(c) for c in mock_print.call_args_list)

        required_fields = [
            "Workspace Metrics (On-Disk)",
            "Token Count:",
            "File Count:",
            "Turn Count:",
        ]
        for field in required_fields:
            self.assertIn(field, all_output, f"Missing required field: '{field}'")


class TestContextStatusOutputContract(unittest.TestCase):
    """Every field in the context status report must be present."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.StateManager')
    @patch('lisa.commands.find_project_root')
    def test_status_report_includes_all_fields(self, mock_root, MockState):
        """context_status output must include: Current Activity."""
        mock_root.return_value = self.test_dir
        MockState.return_value.load.return_value = {"activity": ContextActivity.MONITORING}

        with patch('lisa.commands.print_with_status') as mock_print:
            result = context_status([])

        self.assertEqual(result, 0)

        all_output = " ".join(str(c) for c in mock_print.call_args_list)

        required_fields = [
            "Context System Status",
            "Current Activity:",
        ]
        for field in required_fields:
            self.assertIn(field, all_output, f"Missing required field: '{field}'")


class TestPolishOutputContract(unittest.TestCase):
    """Polish command must output loading msg, skill content, and follow-up."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        skill_dir = os.path.join(self.test_dir, "skills", "polish-pass")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "skill.md"), "w") as f:
            f.write("# Polish Pass\n## Phase 1: Duplicate Detection\n## Phase 2: Naming Audit")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.find_project_root')
    def test_polish_output_includes_all_sections(self, mock_root):
        """polish output must include: loading msg, skill content, separator, follow-up."""
        mock_root.return_value = self.test_dir

        with patch('lisa.commands.print_with_status') as mock_status, \
             patch('builtins.print') as mock_print:
            result = polish([])

        self.assertEqual(result, 0)

        status_output = " ".join(str(c) for c in mock_status.call_args_list)
        print_output = " ".join(str(c) for c in mock_print.call_args_list)

        # Loading message
        self.assertIn("Loading skill instructions", status_output,
                       "Missing loading message")
        # Follow-up prompt
        self.assertIn("Follow the protocol above", status_output,
                       "Missing follow-up prompt")
        # Skill content was printed
        self.assertIn("Polish Pass", print_output,
                       "Skill content not printed")
        # Separator lines
        self.assertIn("=" * 60, print_output,
                       "Missing separator line")


class TestRefactorOutputContract(unittest.TestCase):
    """Refactor command must output loading msg, skill content, and follow-up."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        skill_dir = os.path.join(self.test_dir, "skills", "refactor-gate")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "skill.md"), "w") as f:
            f.write("# Refactor Gate\n## Phase 1: The Refactor Loop\n## Phase 2: Impact Zone")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.find_project_root')
    def test_refactor_output_includes_all_sections(self, mock_root):
        """refactor output must include: loading msg, skill content, separator, follow-up."""
        mock_root.return_value = self.test_dir

        with patch('lisa.commands.print_with_status') as mock_status, \
             patch('builtins.print') as mock_print:
            result = refactor([])

        self.assertEqual(result, 0)

        status_output = " ".join(str(c) for c in mock_status.call_args_list)
        print_output = " ".join(str(c) for c in mock_print.call_args_list)

        # Loading message
        self.assertIn("Loading skill instructions", status_output,
                       "Missing loading message")
        # Follow-up prompt
        self.assertIn("Follow the protocol above", status_output,
                       "Missing follow-up prompt")
        # Skill content was printed
        self.assertIn("Refactor Gate", print_output,
                       "Skill content not printed")
        # Separator lines
        self.assertIn("=" * 60, print_output,
                       "Missing separator line")


class TestDefaultHooksContract(unittest.TestCase):
    """Default lifecycle hook config must match the documented assignments."""

    def test_default_hooks_match_documentation(self):
        """Config defaults must match what's documented in README lifecycle table."""
        from lisa.config import ConfigManager
        defaults = ConfigManager._DEFAULTS["lifecycle_hooks"]

        expected = {
            "story-kickoff": [],
            "story-in-dev": ["lisa turns"],
            "story-test": ["lisa refactor"],
            "story-complete": ["lisa polish"],
            "context-reset": ["lisa checkpoint"],
        }

        self.assertEqual(defaults, expected,
                         "Default hooks have drifted from documented lifecycle table")


if __name__ == "__main__":
    unittest.main()
