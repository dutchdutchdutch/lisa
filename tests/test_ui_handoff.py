"""Tests for UI Test Handoff (Story 7.6).

Covers: handoff trigger (layer gate), scope context output, skill loading,
UI handoff status persistence, and non-blocking completion.
"""
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch

from lisa.scope import (
    load_scope,
    persist_scope,
    update_layer_status,
    get_layer_status,
    record_ui_handoff,
    get_ui_handoff_status,
)


class TestUIHandoffStatus(unittest.TestCase):
    """AC4 (Story 7.6): UI handoff status persistence in scope.json."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_record_ui_handoff_sets_status(self):
        """record_ui_handoff writes 'script_generated' to scope.json."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "modified_files": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)
        record_ui_handoff(self.test_dir)

        data = load_scope(self.test_dir)
        self.assertEqual(data["ui_handoff_status"], "script_generated")

    def test_get_ui_handoff_status_returns_status(self):
        """get_ui_handoff_status reads the persisted status."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "ui_handoff_status": "script_generated",
        }
        persist_scope(self.test_dir, scope)

        status = get_ui_handoff_status(self.test_dir)
        self.assertEqual(status, "script_generated")

    def test_get_ui_handoff_status_defaults_to_pending(self):
        """get_ui_handoff_status returns 'pending' when no status is recorded."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)

        status = get_ui_handoff_status(self.test_dir)
        self.assertEqual(status, "pending")

    def test_get_ui_handoff_status_returns_none_when_no_scope(self):
        """get_ui_handoff_status returns None when no scope is set."""
        status = get_ui_handoff_status(self.test_dir)
        self.assertIsNone(status)


class TestUIHandoffLayerGate(unittest.TestCase):
    """AC1 (Story 7.6): Handoff trigger — all layers must be CLEAN."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        self.skill_dir = os.path.join(self.test_dir, "skills", "ui-handoff")
        os.makedirs(self.skill_dir)
        with open(os.path.join(self.skill_dir, "skill.md"), "w") as f:
            f.write("# UI Handoff Skill\nTest content")
        self._skill_patcher = patch('lisa.commands._SKILL_BASE',
                                     os.path.join(self.test_dir, "skills"))
        self._skill_patcher.start()

    def tearDown(self):
        self._skill_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_blocks_when_unit_not_clean(self):
        """Handoff blocked when UNIT is FAILING (AC1)."""
        from lisa.commands import ui_handoff

        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
            "modified_files": ["src/foo.py"],
            "dependency_cone": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING", failure_count=1)
        update_layer_status(self.test_dir, "INTEGRATION", "CLEAN", failure_count=0)

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("UNIT", all_output)
        self.assertIn("not clean", all_output.lower())

    def test_blocks_when_integration_not_clean(self):
        """Handoff blocked when INTEGRATION is NOT_RUN (AC1)."""
        from lisa.commands import ui_handoff

        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": ["tests/integration/test_a.py"]},
            "modified_files": ["src/foo.py"],
            "dependency_cone": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN", failure_count=0)
        # INTEGRATION defaults to NOT_RUN

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("INTEGRATION", all_output)

    def test_warns_when_no_scope(self):
        """Handoff warns when no scope is set."""
        from lisa.commands import ui_handoff

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("No scope", all_output)

    def test_mode_bypass_skips_gate(self):
        """SPIKE/BYPASS_TDD mode skips the layer gate."""
        from lisa.commands import ui_handoff

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=True), \
             patch('lisa.commands.print_with_status'):
            result = ui_handoff([])

        self.assertEqual(result, 0)

    def test_error_when_skill_missing(self):
        """Returns error when skill.md does not exist."""
        from lisa.commands import ui_handoff

        os.remove(os.path.join(self.skill_dir, "skill.md"))
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "modified_files": ["src/foo.py"],
            "dependency_cone": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN", failure_count=0)
        update_layer_status(self.test_dir, "INTEGRATION", "CLEAN", failure_count=0)

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("not found", all_output.lower())

    def test_no_project_root(self):
        """Returns error when no project root found."""
        from lisa.commands import ui_handoff

        with patch('lisa.commands.find_project_root', side_effect=FileNotFoundError), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("project root", all_output.lower())


class TestUIHandoffOutput(unittest.TestCase):
    """AC2/AC4 (Story 7.6): Context output, skill loading, and status recording."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        self.skill_dir = os.path.join(self.test_dir, "skills", "ui-handoff")
        os.makedirs(self.skill_dir)
        with open(os.path.join(self.skill_dir, "skill.md"), "w") as f:
            f.write("# UI Handoff Skill\nTest content about UI verification")
        self._skill_patcher = patch('lisa.commands._SKILL_BASE',
                                     os.path.join(self.test_dir, "skills"))
        self._skill_patcher.start()

    def tearDown(self):
        self._skill_patcher.stop()
        shutil.rmtree(self.test_dir)

    def _setup_clean_scope(self, modified_files=None, dependency_cone=None):
        """Helper to create a scope with all layers CLEAN."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
            "modified_files": modified_files or ["src/foo.py"],
            "dependency_cone": dependency_cone or ["src/foo.py", "src/bar.py"],
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN", failure_count=0)
        update_layer_status(self.test_dir, "INTEGRATION", "CLEAN", failure_count=0)

    def test_outputs_modified_files(self):
        """Handoff output includes modified files from scope (AC2)."""
        from lisa.commands import ui_handoff

        self._setup_clean_scope(modified_files=["src/commands.py", "src/scope.py"])

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("src/commands.py", all_output)
        self.assertIn("src/scope.py", all_output)

    def test_outputs_skill_content(self):
        """Handoff output includes skill.md content (AC2/AC3)."""
        from lisa.commands import ui_handoff

        self._setup_clean_scope()

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print, \
             patch('builtins.print') as mock_bare_print:
            result = ui_handoff([])

        self.assertEqual(result, 0)
        bare_output = " ".join(str(c) for c in mock_bare_print.call_args_list)
        self.assertIn("UI Handoff Skill", bare_output)

    def test_records_handoff_status(self):
        """Handoff records 'script_generated' in scope.json (AC4)."""
        from lisa.commands import ui_handoff

        self._setup_clean_scope()

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status'):
            result = ui_handoff([])

        self.assertEqual(result, 0)
        status = get_ui_handoff_status(self.test_dir)
        self.assertEqual(status, "script_generated")

    def test_outputs_pending_note(self):
        """Handoff output includes non-blocking completion note (AC4)."""
        from lisa.commands import ui_handoff

        self._setup_clean_scope()

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("ui verification pending", all_output.lower())

    def test_allows_layers_clean_with_no_tests(self):
        """Handoff succeeds when layers are clean with no in-scope tests."""
        from lisa.commands import ui_handoff

        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "modified_files": ["src/foo.py"],
            "dependency_cone": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN", failure_count=0)
        update_layer_status(self.test_dir, "INTEGRATION", "CLEAN", failure_count=0)

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status'):
            result = ui_handoff([])

        self.assertEqual(result, 0)


class TestUIHandoffIntegration(unittest.TestCase):
    """Integration (Story 7.6): Full flow across verify-layer and ui-handoff."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        self.skill_dir = os.path.join(self.test_dir, "skills", "ui-handoff")
        os.makedirs(self.skill_dir)
        with open(os.path.join(self.skill_dir, "skill.md"), "w") as f:
            f.write("# UI Handoff Skill\nGenerate manual test script")
        self._skill_patcher = patch('lisa.commands._SKILL_BASE',
                                     os.path.join(self.test_dir, "skills"))
        self._skill_patcher.start()

    def tearDown(self):
        self._skill_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_full_flow_layers_clean_then_handoff(self):
        """Full flow: UNIT clean, INTEGRATION clean, then handoff succeeds."""
        from lisa.commands import verify_layer, ui_handoff

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": ["tests/integration/test_b.py"],
            },
            "modified_files": ["src/foo.py"],
            "dependency_cone": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)

        # UNIT passes
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=0), \
             patch('lisa.commands.print_with_status'):
            verify_layer(["unit"])

        # INTEGRATION passes
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=0), \
             patch('lisa.commands.print_with_status'):
            verify_layer(["integration"])

        # Handoff succeeds
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])

        self.assertEqual(result, 0)
        self.assertEqual(get_ui_handoff_status(self.test_dir), "script_generated")
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("src/foo.py", all_output)

    def test_handoff_blocked_then_succeeds_after_fix(self):
        """Handoff blocked by UNIT failure, then succeeds after fix."""
        from lisa.commands import verify_layer, ui_handoff

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
            "modified_files": ["src/foo.py"],
            "dependency_cone": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)

        # UNIT fails
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=1), \
             patch('lisa.commands.print_with_status'):
            verify_layer(["unit"])

        # Handoff blocked
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = ui_handoff([])
        self.assertEqual(result, 1)

        # Fix UNIT
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=0), \
             patch('lisa.commands.print_with_status'):
            verify_layer(["unit"])

        # Set INTEGRATION to CLEAN (no integration tests)
        update_layer_status(self.test_dir, "INTEGRATION", "CLEAN", failure_count=0)

        # Handoff now succeeds
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.print_with_status'):
            result = ui_handoff([])
        self.assertEqual(result, 0)
        self.assertEqual(get_ui_handoff_status(self.test_dir), "script_generated")


if __name__ == "__main__":
    unittest.main()
