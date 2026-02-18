"""Tests for out-of-scope failure deferral (Story 7.4).

Covers: failure classification (AC1), deferred display (AC2),
layer decision ignoring out-of-scope failures (AC3),
and deferral record persistence (AC4).
"""
import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch

from lisa.scope import (
    persist_scope,
    load_scope,
    get_layer_status,
    update_layer_status,
    get_all_tests_for_layer,
    record_deferred_failures,
    get_deferred_failures,
)
from lisa.classifier import persist_layers


# ---------------------------------------------------------------------------
# scope.py unit tests — new functions for Story 7.4
# ---------------------------------------------------------------------------

class TestGetAllTestsForLayer(unittest.TestCase):
    """get_all_tests_for_layer returns every classified test file for a layer."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_returns_unit_tests_from_layers_json(self):
        """Returns all UNIT test files from layers.json."""
        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/integration/test_c.py", "layer": "INTEGRATION", "subtype": None, "method": "path_pattern"},
        ]
        persist_layers(self.test_dir, layers)
        result = get_all_tests_for_layer(self.test_dir, "UNIT")
        self.assertEqual(result, ["tests/test_a.py", "tests/test_b.py"])

    def test_returns_integration_tests_from_layers_json(self):
        """Returns all INTEGRATION test files from layers.json."""
        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/integration/test_c.py", "layer": "INTEGRATION", "subtype": None, "method": "path_pattern"},
            {"file": "tests/integration/test_d.py", "layer": "INTEGRATION", "subtype": "API", "method": "path_pattern"},
        ]
        persist_layers(self.test_dir, layers)
        result = get_all_tests_for_layer(self.test_dir, "INTEGRATION")
        self.assertEqual(result, ["tests/integration/test_c.py", "tests/integration/test_d.py"])

    def test_returns_empty_when_no_tests_for_layer(self):
        """Returns empty list when no tests exist for the requested layer."""
        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)
        result = get_all_tests_for_layer(self.test_dir, "INTEGRATION")
        self.assertEqual(result, [])

    def test_returns_none_when_no_layers_json(self):
        """Returns None when layers.json does not exist."""
        result = get_all_tests_for_layer(self.test_dir, "UNIT")
        self.assertIsNone(result)


class TestRecordDeferredFailures(unittest.TestCase):
    """record_deferred_failures persists out-of-scope failures into scope.json."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_records_failures_for_layer(self):
        """Deferred failures are stored under deferred_failures.<layer>."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        record_deferred_failures(self.test_dir, "UNIT", ["tests/test_x.py", "tests/test_y.py"])

        data = load_scope(self.test_dir)
        self.assertEqual(
            data["deferred_failures"]["UNIT"],
            ["tests/test_x.py", "tests/test_y.py"],
        )

    def test_preserves_existing_scope_data(self):
        """Recording deferred failures does not clobber other scope fields."""
        scope = {
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
            "modified_files": ["src/foo.py"],
        }
        persist_scope(self.test_dir, scope)
        record_deferred_failures(self.test_dir, "UNIT", ["tests/test_x.py"])

        data = load_scope(self.test_dir)
        self.assertEqual(data["modified_files"], ["src/foo.py"])
        self.assertEqual(data["in_scope_tests"]["UNIT"], ["tests/test_a.py"])

    def test_replaces_previous_deferred_for_same_layer(self):
        """Re-recording deferred failures for the same layer replaces old values."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        record_deferred_failures(self.test_dir, "UNIT", ["tests/test_old.py"])
        record_deferred_failures(self.test_dir, "UNIT", ["tests/test_new.py"])

        data = load_scope(self.test_dir)
        self.assertEqual(data["deferred_failures"]["UNIT"], ["tests/test_new.py"])

    def test_records_empty_list_clears_deferred(self):
        """Recording an empty list clears deferred failures for the layer."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        record_deferred_failures(self.test_dir, "UNIT", ["tests/test_x.py"])
        record_deferred_failures(self.test_dir, "UNIT", [])

        data = load_scope(self.test_dir)
        self.assertEqual(data["deferred_failures"]["UNIT"], [])

    def test_noop_when_no_scope(self):
        """Does nothing when no scope is set (fail-safe)."""
        record_deferred_failures(self.test_dir, "UNIT", ["tests/test_x.py"])
        data = load_scope(self.test_dir)
        self.assertIsNone(data)


class TestGetDeferredFailures(unittest.TestCase):
    """get_deferred_failures retrieves deferred failures from scope.json."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_returns_deferred_failures(self):
        """Returns the deferred_failures dict from scope.json."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "deferred_failures": {
                "UNIT": ["tests/test_x.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)
        result = get_deferred_failures(self.test_dir)
        self.assertEqual(result, {"UNIT": ["tests/test_x.py"], "INTEGRATION": []})

    def test_returns_empty_dict_when_no_deferred(self):
        """Returns empty dict when no deferred failures are recorded."""
        scope = {
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
        }
        persist_scope(self.test_dir, scope)
        result = get_deferred_failures(self.test_dir)
        self.assertEqual(result, {})

    def test_returns_none_when_no_scope(self):
        """Returns None when no scope is set."""
        result = get_deferred_failures(self.test_dir)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# commands.py tests — verify_layer with failure deferral
# ---------------------------------------------------------------------------

class TestVerifyLayerFailureClassification(unittest.TestCase):
    """AC1: Failures are classified as IN_SCOPE or OUT_OF_SCOPE."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_runs_all_tests_for_layer(self):
        """verify_layer runs all classified tests for the layer, not just in-scope."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_c.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=0) as mock_run, \
             patch('lisa.commands.print_with_status'):
            verify_layer(["unit"])

        # All 3 tests should be run, not just the 1 in-scope test
        self.assertEqual(mock_run.call_count, 3)

    def test_in_scope_failure_classified_correctly(self):
        """In-scope test failure appears in main failure output."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # test_a fails (in-scope), test_b passes (out-of-scope)
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', side_effect=lambda f: 1 if f == "tests/test_a.py" else 0), \
             patch('lisa.commands.print_with_status') as mock_print:
            result = verify_layer(["unit"])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("test_a.py", all_output)

    def test_out_of_scope_failure_classified_as_deferred(self):
        """Out-of-scope test failure appears in deferred section, not main output."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # test_a passes (in-scope), test_b fails (out-of-scope)
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', side_effect=lambda f: 1 if f == "tests/test_b.py" else 0), \
             patch('lisa.commands.print_with_status') as mock_print:
            verify_layer(["unit"])

        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("Deferred", all_output)
        self.assertIn("test_b.py", all_output)


class TestVerifyLayerDeferredDisplay(unittest.TestCase):
    """AC2: Deferred failures display in a separate section with instructions."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_deferred_section_includes_instruction(self):
        """Deferred section tells the agent not to fix these failures."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_out.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # Out-of-scope test fails
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', side_effect=lambda f: 1 if f == "tests/test_out.py" else 0), \
             patch('lisa.commands.print_with_status') as mock_print:
            verify_layer(["unit"])

        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("outside story scope", all_output.lower())
        self.assertIn("do not fix", all_output.lower())

    def test_no_deferred_section_when_no_out_of_scope_failures(self):
        """No deferred section appears when all failures are in-scope."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # In-scope test fails
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=1), \
             patch('lisa.commands.print_with_status') as mock_print:
            verify_layer(["unit"])

        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertNotIn("Deferred", all_output)


class TestVerifyLayerDecision(unittest.TestCase):
    """AC3: Only in-scope failures count for layer pass/fail."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_out_of_scope_failures_do_not_block(self):
        """Layer is CLEAN when only out-of-scope tests fail (AC3)."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # In-scope passes, out-of-scope fails
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', side_effect=lambda f: 1 if f == "tests/test_b.py" else 0), \
             patch('lisa.commands.print_with_status'):
            result = verify_layer(["unit"])

        self.assertEqual(result, 0)
        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "CLEAN")

    def test_in_scope_failure_still_blocks(self):
        """Layer is FAILING when in-scope test fails, even if out-of-scope also fails."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # Both fail
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=1), \
             patch('lisa.commands.print_with_status'):
            result = verify_layer(["unit"])

        self.assertEqual(result, 1)
        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "FAILING")

    def test_all_pass_returns_clean(self):
        """Layer is CLEAN when all tests pass (in-scope and out-of-scope)."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=0), \
             patch('lisa.commands.print_with_status'):
            result = verify_layer(["unit"])

        self.assertEqual(result, 0)
        status = get_layer_status(self.test_dir)
        self.assertEqual(status["UNIT"], "CLEAN")


class TestVerifyLayerDeferralRecord(unittest.TestCase):
    """AC4: Deferred failures are recorded for downstream reporting."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_deferred_failures_persisted_to_scope(self):
        """Out-of-scope failures are recorded in scope.json deferred_failures."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_c.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # In-scope passes, two out-of-scope fail
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', side_effect=lambda f: 0 if f == "tests/test_a.py" else 1), \
             patch('lisa.commands.print_with_status'):
            verify_layer(["unit"])

        deferred = get_deferred_failures(self.test_dir)
        self.assertIn("UNIT", deferred)
        self.assertEqual(sorted(deferred["UNIT"]), ["tests/test_b.py", "tests/test_c.py"])

    def test_no_deferred_failures_recorded_when_none(self):
        """No deferred failures recorded when all failures are in-scope."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # In-scope fails, no out-of-scope tests
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=1), \
             patch('lisa.commands.print_with_status'):
            verify_layer(["unit"])

        deferred = get_deferred_failures(self.test_dir)
        self.assertEqual(deferred.get("UNIT", []), [])

    def test_deferred_cleared_on_clean_run(self):
        """Previously deferred failures are cleared when a clean run has none."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
            "deferred_failures": {
                "UNIT": ["tests/test_b.py"],
            },
        }
        persist_scope(self.test_dir, scope)

        layers = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/test_b.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        persist_layers(self.test_dir, layers)

        # All pass now
        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=0), \
             patch('lisa.commands.print_with_status'):
            verify_layer(["unit"])

        deferred = get_deferred_failures(self.test_dir)
        self.assertEqual(deferred.get("UNIT", []), [])


class TestVerifyLayerFallbackWithoutLayers(unittest.TestCase):
    """When layers.json is missing, verify_layer falls back to in-scope-only behavior."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_fallback_to_in_scope_only(self):
        """Without layers.json, verify_layer runs only in-scope tests."""
        from lisa.commands import verify_layer

        scope = {
            "in_scope_tests": {
                "UNIT": ["tests/test_a.py"],
                "INTEGRATION": [],
            },
        }
        persist_scope(self.test_dir, scope)
        # No layers.json persisted

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.check_mode_bypass', return_value=False), \
             patch('lisa.commands.run_test', return_value=0) as mock_run, \
             patch('lisa.commands.print_with_status'):
            result = verify_layer(["unit"])

        self.assertEqual(result, 0)
        # Only the 1 in-scope test should run (no layers.json to expand from)
        self.assertEqual(mock_run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
