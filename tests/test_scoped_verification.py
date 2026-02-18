"""Tests for scoped verification / layer gate (Stories 7.3, 7.5).

Covers: layer-scoped execution, layer advancement/blocking, backwards
compatibility (explicit files + out-of-scope warning), no-scope fallback,
layer status tracking, failure count persistence, fix-at-layer guidance,
and layer progression gate enforcement.
"""
import unittest
import os
import json
import tempfile
import shutil

from scripts.lisa.scope import (
    load_scope,
    persist_scope,
    get_layer_status,
    update_layer_status,
    get_in_scope_tests_for_layer,
    check_layer_advancement,
    get_layer_failure_counts,
)


class TestGetInScopeTestsForLayer(unittest.TestCase):
    """AC1: Layer-scoped execution — extracting tests for a specific layer."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_returns_unit_tests_only(self):
        """When layer is UNIT, only in-scope UNIT tests are returned."""
        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py", "tests/test_b.py"],
                "INTEGRATION": ["tests/integration/test_c.py"],
            }
        }
        persist_scope(self.test_dir, scope)
        tests = get_in_scope_tests_for_layer(self.test_dir, "UNIT")
        self.assertEqual(tests, ["tests/test_a.py", "tests/test_b.py"])

    def test_returns_integration_tests_only(self):
        """When layer is INTEGRATION, only in-scope INTEGRATION tests are returned."""
        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": ["tests/integration/test_c.py"],
            }
        }
        persist_scope(self.test_dir, scope)
        tests = get_in_scope_tests_for_layer(self.test_dir, "INTEGRATION")
        self.assertEqual(tests, ["tests/integration/test_c.py"])

    def test_returns_empty_when_no_tests_for_layer(self):
        """Returns empty list when no in-scope tests exist for the layer."""
        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            }
        }
        persist_scope(self.test_dir, scope)
        tests = get_in_scope_tests_for_layer(self.test_dir, "INTEGRATION")
        self.assertEqual(tests, [])

    def test_returns_none_when_no_scope(self):
        """Returns None when no scope is set."""
        tests = get_in_scope_tests_for_layer(self.test_dir, "UNIT")
        self.assertIsNone(tests)


class TestLayerStatus(unittest.TestCase):
    """AC1/AC2: Layer status tracking and persistence."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_default_status_is_not_run(self):
        """Layers default to NOT_RUN when no status is set."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "NOT_RUN")
        self.assertEqual(status["INTEGRATION"], "NOT_RUN")

    def test_update_layer_status_persists(self):
        """update_layer_status writes the status into scope.json."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")

        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "CLEAN")

    def test_update_preserves_other_layer(self):
        """Updating UNIT status does not affect INTEGRATION status."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")
        update_layer_status(self.test_dir, "INTEGRATION", "FAILING")

        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "CLEAN")
        self.assertEqual(status["INTEGRATION"], "FAILING")

    def test_status_returns_none_when_no_scope(self):
        """get_layer_status returns None when no scope is set."""
        status = get_layer_status(self.test_dir)
        self.assertIsNone(status)

    def test_update_layer_status_persists_failure_count(self):
        """update_layer_status stores the failure count in scope.json (Story 7.5 AC3)."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING", failure_count=3)

        data = load_scope(self.test_dir)
        self.assertEqual(data["layer_failure_counts"]["UNIT"], 3)

    def test_update_layer_status_clean_clears_failure_count(self):
        """Setting CLEAN clears the failure count for that layer (Story 7.5 AC3)."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING", failure_count=3)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")

        data = load_scope(self.test_dir)
        self.assertEqual(data["layer_failure_counts"].get("UNIT", 0), 0)

    def test_update_layer_status_without_count_preserves_existing(self):
        """Calling without failure_count does not clobber existing counts (Story 7.5 AC3)."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING", failure_count=3)
        # Old-style call (no count) -- backwards compatibility
        update_layer_status(self.test_dir, "INTEGRATION", "NOT_RUN")

        data = load_scope(self.test_dir)
        # UNIT count should be preserved
        self.assertEqual(data["layer_failure_counts"]["UNIT"], 3)

    def test_get_layer_failure_counts_returns_counts(self):
        """get_layer_failure_counts returns persisted failure counts (Story 7.5 AC3)."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING", failure_count=5)

        counts = get_layer_failure_counts(self.test_dir)
        self.assertEqual(counts["UNIT"], 5)
        self.assertEqual(counts.get("INTEGRATION", 0), 0)

    def test_get_layer_failure_counts_returns_none_when_no_scope(self):
        """get_layer_failure_counts returns None when no scope is set (Story 7.5 AC3)."""
        counts = get_layer_failure_counts(self.test_dir)
        self.assertIsNone(counts)

    def test_get_layer_failure_counts_defaults_to_empty(self):
        """get_layer_failure_counts returns empty dict for scope with no counts (Story 7.5 AC3)."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)

        counts = get_layer_failure_counts(self.test_dir)
        self.assertEqual(counts.get("UNIT", 0), 0)


class TestCheckLayerAdvancement(unittest.TestCase):
    """AC2: Layer advancement — UNIT must be clean before INTEGRATION."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_blocks_integration_when_unit_not_run(self):
        """Cannot advance to INTEGRATION when UNIT is NOT_RUN."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": ["tests/integration/test_b.py"]},
        }
        persist_scope(self.test_dir, scope)
        allowed, reason = check_layer_advancement(self.test_dir, "INTEGRATION")
        self.assertFalse(allowed)
        self.assertIn("UNIT", reason)

    def test_blocks_integration_when_unit_failing(self):
        """Cannot advance to INTEGRATION when UNIT is FAILING."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": ["tests/integration/test_b.py"]},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING")
        allowed, reason = check_layer_advancement(self.test_dir, "INTEGRATION")
        self.assertFalse(allowed)
        self.assertIn("UNIT", reason)

    def test_allows_integration_when_unit_clean(self):
        """Can advance to INTEGRATION when UNIT is CLEAN."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": ["tests/integration/test_b.py"]},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")
        allowed, reason = check_layer_advancement(self.test_dir, "INTEGRATION")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_allows_unit_always(self):
        """UNIT layer is always allowed (no prerequisite layer)."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        allowed, reason = check_layer_advancement(self.test_dir, "UNIT")
        self.assertTrue(allowed)

    def test_allows_integration_when_no_unit_tests(self):
        """If no UNIT tests are in scope, INTEGRATION is allowed (nothing to block on)."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": ["tests/integration/test_b.py"]},
        }
        persist_scope(self.test_dir, scope)
        allowed, reason = check_layer_advancement(self.test_dir, "INTEGRATION")
        self.assertTrue(allowed)

    def test_returns_not_allowed_when_no_scope(self):
        """Returns not-allowed when no scope is set."""
        allowed, reason = check_layer_advancement(self.test_dir, "UNIT")
        self.assertFalse(allowed)
        self.assertIn("No scope", reason)

    def test_blocks_integration_message_includes_failure_count(self):
        """Block message includes the failure count when available (Story 7.5 AC1)."""
        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py", "tests/test_b.py"],
                "INTEGRATION": ["tests/integration/test_c.py"],
            },
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING", failure_count=2)

        allowed, reason = check_layer_advancement(self.test_dir, "INTEGRATION")
        self.assertFalse(allowed)
        self.assertIn("2", reason)
        self.assertIn("in-scope failure", reason.lower())


class TestVerifyLayerCommand(unittest.TestCase):
    """AC1/AC2/AC4: The lisa verify-layer CLI command."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_no_scope_returns_warning(self):
        """lisa verify-layer unit warns when no scope is set (AC4)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["unit"])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("No scope", all_output)

    def test_no_args_shows_usage(self):
        """lisa verify-layer without args shows usage."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer([])

        self.assertEqual(result, 1)

    def test_blocks_integration_when_unit_not_clean(self):
        """lisa verify-layer integration is blocked when UNIT is not CLEAN (AC2)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": ["tests/integration/test_b.py"],
            },
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["integration"])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("UNIT", all_output)

    def test_runs_scoped_unit_tests(self):
        """lisa verify-layer unit runs only in-scope UNIT tests (AC1)."""
        from unittest.mock import patch, call
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py", "tests/test_b.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0) as mock_run, \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["unit"])

        self.assertEqual(result, 0)
        # Both unit tests should have been run
        self.assertEqual(mock_run.call_count, 2)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("UNIT", all_output)
        self.assertIn("2", all_output)  # number of tests

    def test_layer_status_updated_to_clean(self):
        """Layer status is set to CLEAN when all tests pass (AC1)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.print_with_status'):
            verify_layer(["unit"])

        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "CLEAN")

    def test_layer_status_updated_to_failing(self):
        """Layer status is set to FAILING when a test fails (AC1)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py", "tests/test_b.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        # First test passes, second fails
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', side_effect=[0, 1]), \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer(["unit"])

        self.assertEqual(result, 1)
        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "FAILING")

    def test_layer_status_failing_includes_count(self):
        """When in-scope tests fail, the failure count is persisted (Story 7.5 AC3)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py", "tests/test_b.py", "tests/test_c.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        # First and third tests fail (2 in-scope failures)
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', side_effect=[1, 0, 1]), \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer(["unit"])

        self.assertEqual(result, 1)
        counts = get_layer_failure_counts(self.test_dir)
        self.assertEqual(counts["UNIT"], 2)

    def test_layer_status_clean_sets_count_zero(self):
        """When all in-scope tests pass, the failure count is 0 (Story 7.5 AC3)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.print_with_status'):
            verify_layer(["unit"])

        counts = get_layer_failure_counts(self.test_dir)
        self.assertEqual(counts.get("UNIT", 0), 0)

    def test_integration_runs_after_unit_clean(self):
        """lisa verify-layer integration runs when UNIT is CLEAN (AC2)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": ["tests/integration/test_b.py"],
            },
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0) as mock_run, \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer(["integration"])

        self.assertEqual(result, 0)
        self.assertEqual(mock_run.call_count, 1)

    def test_mode_bypass_skips_verification(self):
        """verify-layer respects SPIKE/BYPASS_TDD modes."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=True), \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer(["unit"])

        self.assertEqual(result, 0)


class TestBackwardsCompatibility(unittest.TestCase):
    """AC3: Explicit file in verify-fail/verify-pass still works, with scope warning."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_verify_pass_explicit_file_with_scope_warning(self):
        """verify-pass with explicit file works but warns if outside scope (AC3)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_pass

        # Set a scope that does NOT include the explicit file
        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
            "dependency_cone": ["src/a.py"],
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.run_story_complete'), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_pass(["tests/test_unrelated.py"])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("outside", all_output.lower())

    def test_verify_pass_explicit_file_in_scope_no_warning(self):
        """verify-pass with explicit file in scope does not warn."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_pass

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
            "dependency_cone": ["src/a.py"],
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.run_story_complete'), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_pass(["tests/test_a.py"])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertNotIn("outside", all_output.lower())

    def test_verify_fail_explicit_file_outside_scope_warns(self):
        """verify-fail with explicit file outside scope emits warning (AC3)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_fail

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
            "dependency_cone": ["src/a.py"],
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=1), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_fail(["tests/test_unrelated.py"])

        self.assertEqual(result, 0)  # Test failed as expected = success
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("outside", all_output.lower())

    def test_verify_pass_no_scope_no_warning(self):
        """verify-pass without scope does not emit scope warning (AC3 backwards compat)."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_pass

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.run_story_complete'), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_pass(["tests/test_a.py"])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertNotIn("outside", all_output.lower())


class TestLayerStatusCommand(unittest.TestCase):
    """AC2: lisa layer-status displays current state of each layer."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_shows_both_layers(self):
        """lisa layer-status shows UNIT and INTEGRATION states."""
        from unittest.mock import patch
        from scripts.lisa.commands import layer_status_cmd

        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = layer_status_cmd([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("UNIT", all_output)
        self.assertIn("CLEAN", all_output)
        self.assertIn("INTEGRATION", all_output)
        self.assertIn("NOT_RUN", all_output)

    def test_warns_when_no_scope(self):
        """lisa layer-status warns when no scope is set."""
        from unittest.mock import patch
        from scripts.lisa.commands import layer_status_cmd

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = layer_status_cmd([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("No scope", all_output)

    def test_shows_failure_count_when_failing(self):
        """lisa layer-status shows failure count when layer is FAILING (Story 7.5 AC3)."""
        from unittest.mock import patch
        from scripts.lisa.commands import layer_status_cmd

        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "FAILING", failure_count=3)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = layer_status_cmd([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("FAILING", all_output)
        self.assertIn("3", all_output)
        self.assertIn("in-scope", all_output.lower())

    def test_shows_clean_without_failure_count(self):
        """lisa layer-status shows CLEAN without a failure count (Story 7.5 AC3)."""
        from unittest.mock import patch
        from scripts.lisa.commands import layer_status_cmd

        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN", failure_count=0)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = layer_status_cmd([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("CLEAN", all_output)
        self.assertNotIn("in-scope failure", all_output.lower())


class TestLayerProgressionIntegration(unittest.TestCase):
    """Integration (Story 7.5): Full layer progression flow across commands and scope."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_progression_unit_fail_block_fix_advance(self):
        """Full flow: UNIT fails -> blocks INTEGRATION -> UNIT passes -> INTEGRATION runs."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer, layer_status_cmd

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py", "tests/test_b.py"],
                "INTEGRATION": ["tests/integration/test_c.py"],
            },
        }
        persist_scope(self.test_dir, scope)

        # Phase 1: UNIT fails — one of two tests fails
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', side_effect=[0, 1]), \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer(["unit"])
        self.assertEqual(result, 1)

        # Verify layer status shows FAILING with count
        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "FAILING")
        counts = get_layer_failure_counts(self.test_dir)
        self.assertEqual(counts["UNIT"], 1)

        # Phase 2: Attempt INTEGRATION — blocked by UNIT gate
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["integration"])
        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("UNIT", all_output)
        self.assertIn("1 in-scope failure", all_output.lower())

        # Phase 3: Fix and re-run UNIT — passes
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer(["unit"])
        self.assertEqual(result, 0)
        self.assertEqual(get_layer_status(self.test_dir)["UNIT"], "CLEAN")

        # Phase 4: INTEGRATION now allowed
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.print_with_status'):
            result = verify_layer(["integration"])
        self.assertEqual(result, 0)
        self.assertEqual(get_layer_status(self.test_dir)["INTEGRATION"], "CLEAN")

    def test_integration_failure_shows_guidance_and_status(self):
        """INTEGRATION fails -> fix-at-layer guidance + layer-status shows count."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer, layer_status_cmd

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": ["tests/integration/test_b.py", "tests/integration/test_c.py"],
            },
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN", failure_count=0)

        # INTEGRATION: both tests fail
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=1), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["integration"])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("fix at the integration layer", all_output.lower())
        self.assertIn("do not revisit unit", all_output.lower())

        # layer-status reflects the count
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            layer_status_cmd([])

        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("FAILING", all_output)
        self.assertIn("2 in-scope failures", all_output.lower())
        # UNIT should still show CLEAN
        self.assertIn("CLEAN", all_output)

    def test_layer_status_reflects_full_lifecycle(self):
        """layer-status shows NOT_RUN -> FAILING -> CLEAN through a complete cycle."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer, layer_status_cmd

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        # Initial: both NOT_RUN
        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "NOT_RUN")
        self.assertEqual(status["INTEGRATION"], "NOT_RUN")

        # UNIT fails
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=1), \
             patch('scripts.lisa.commands.print_with_status'):
            verify_layer(["unit"])

        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "FAILING")
        counts = get_layer_failure_counts(self.test_dir)
        self.assertEqual(counts["UNIT"], 1)

        # UNIT passes
        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.print_with_status'):
            verify_layer(["unit"])

        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "CLEAN")
        counts = get_layer_failure_counts(self.test_dir)
        self.assertEqual(counts["UNIT"], 0)


class TestFixAtLayerGuidance(unittest.TestCase):
    """AC2 (Story 7.5): When INTEGRATION fails, instruct to fix at integration layer."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_failure_emits_fix_at_layer_guidance(self):
        """When INTEGRATION layer has in-scope failures, fix-at-layer guidance is emitted."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": ["tests/integration/test_b.py"],
            },
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=1), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["integration"])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("fix at the integration layer", all_output.lower())
        self.assertIn("do not revisit unit", all_output.lower())

    def test_unit_failure_does_not_emit_fix_at_layer_guidance(self):
        """When UNIT layer fails, no fix-at-layer guidance is emitted."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=1), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["unit"])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertNotIn("fix at the integration layer", all_output.lower())

    def test_integration_clean_does_not_emit_guidance(self):
        """When INTEGRATION passes, no fix-at-layer guidance is emitted."""
        from unittest.mock import patch
        from scripts.lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": ["tests/integration/test_b.py"],
            },
        }
        persist_scope(self.test_dir, scope)
        update_layer_status(self.test_dir, "UNIT", "CLEAN")

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.check_mode_bypass', return_value=False), \
             patch('scripts.lisa.commands.run_test', return_value=0), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["integration"])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertNotIn("fix at the integration layer", all_output.lower())


if __name__ == "__main__":
    unittest.main()
