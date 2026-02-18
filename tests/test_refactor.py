"""Tests for the lisa refactor command."""
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch

from lisa.commands import refactor


class TestRefactor(unittest.TestCase):
    """Tests for the refactor command."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(self.lisa_dir)
        self.skill_dir = os.path.join(self.test_dir, "skills", "refactor-gate")
        os.makedirs(self.skill_dir)
        with open(os.path.join(self.skill_dir, "skill.md"), "w") as f:
            f.write("# Refactor Gate Skill\nTest content")
        self._skill_patcher = patch('lisa.commands._SKILL_BASE',
                                     os.path.join(self.test_dir, "skills"))
        self._skill_patcher.start()

    def tearDown(self):
        self._skill_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.print_with_status')
    def test_refactor_outputs_skill(self, mock_print, mock_root):
        """Should print skill.md content when skill exists."""
        mock_root.return_value = self.test_dir
        result = refactor([])
        self.assertEqual(result, 0)
        mock_print.assert_any_call("Refactor Gate: Loading skill instructions...", status_icon="🔧")

    @patch('lisa.commands.find_project_root')
    @patch('lisa.commands.print_with_status')
    def test_refactor_missing_skill(self, mock_print, mock_root):
        """Should return error when skill.md does not exist."""
        mock_root.return_value = self.test_dir
        os.remove(os.path.join(self.skill_dir, "skill.md"))
        result = refactor([])
        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("Refactor Gate skill not found", all_output)

    @patch('lisa.commands.find_project_root', side_effect=FileNotFoundError)
    @patch('lisa.commands.print_with_status')
    def test_refactor_no_project_root(self, mock_print, mock_root):
        """Should return error when no project root found."""
        result = refactor([])
        self.assertEqual(result, 1)
        mock_print.assert_any_call("Error: Could not determine project root.", status_icon="🔴")


if __name__ == "__main__":
    unittest.main()
