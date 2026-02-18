"""Tests for test layer classification (Story 7.1).

Covers: discover_test_files, classify_file, classify_all, persist/load_layers,
custom rules, path patterns, naming conventions, markers, default fallback,
and integration sub-type detection.
"""
import unittest
import os
import json
import tempfile
import shutil

from lisa.classifier import (
    discover_test_files,
    classify_file,
    classify_all,
    persist_layers,
    load_layers,
    LAYER_UNIT,
    LAYER_INTEGRATION,
    SUBTYPE_CONTRACT,
    SUBTYPE_API,
    SUBTYPE_PACT,
    SUBTYPE_COMPONENT,
)


class TestDiscoverTestFiles(unittest.TestCase):
    """AC1/AC3: Discovery of test files in the project."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_discovers_test_prefixed_files(self):
        """Files named test_*.py are discovered."""
        self._create_file("tests/test_foo.py")
        self._create_file("tests/test_bar.py")
        result = discover_test_files(self.test_dir)
        self.assertEqual(len(result), 2)
        self.assertIn(os.path.join("tests", "test_foo.py"), result)

    def test_discovers_test_suffixed_files(self):
        """Files named *_test.py are discovered."""
        self._create_file("tests/foo_test.py")
        result = discover_test_files(self.test_dir)
        self.assertEqual(len(result), 1)
        self.assertIn(os.path.join("tests", "foo_test.py"), result)

    def test_ignores_non_test_files(self):
        """Non-test Python files and non-Python files are not discovered."""
        self._create_file("scripts/main.py")
        self._create_file("tests/helper.py")
        self._create_file("tests/README.md")
        result = discover_test_files(self.test_dir)
        self.assertEqual(len(result), 0)

    def test_ignores_dotdirs(self):
        """Files under .git, .lisa, __pycache__ are not discovered."""
        self._create_file(".git/test_hooks.py")
        self._create_file(".lisa/test_state.py")
        self._create_file("__pycache__/test_cache.py")
        result = discover_test_files(self.test_dir)
        self.assertEqual(len(result), 0)

    def test_discovers_nested_test_files(self):
        """Test files in subdirectories are discovered."""
        self._create_file("tests/unit/test_a.py")
        self._create_file("tests/integration/test_b.py")
        result = discover_test_files(self.test_dir)
        self.assertEqual(len(result), 2)


class TestClassifyFileDefault(unittest.TestCase):
    """AC1/AC2: Default classification — unmatched files go to UNIT."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = {"test_layers": {
            "integration_path_patterns": ["tests/integration/"],
            "integration_name_patterns": ["*_contract_test.py"],
            "custom_rules": {}
        }}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_flat_test_file_defaults_to_unit(self):
        """A test file in tests/ with no matching integration rule defaults to UNIT."""
        self._create_file("tests/test_utils.py", "import unittest")
        result = classify_file(os.path.join("tests", "test_utils.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_UNIT)
        self.assertEqual(result["method"], "default")
        self.assertIsNone(result["subtype"])

    def test_result_contains_required_keys(self):
        """Classification result always has file, layer, subtype, method."""
        self._create_file("tests/test_x.py")
        result = classify_file(os.path.join("tests", "test_x.py"), self.config, self.test_dir)
        self.assertIn("file", result)
        self.assertIn("layer", result)
        self.assertIn("subtype", result)
        self.assertIn("method", result)


class TestClassifyFilePathPatterns(unittest.TestCase):
    """AC1: Path pattern classification."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = {"test_layers": {
            "integration_path_patterns": [
                "tests/integration/",
                "tests/api/",
                "tests/contract/",
                "tests/pact/",
                "tests/component/"
            ],
            "integration_name_patterns": [],
            "custom_rules": {}
        }}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_integration_path_classifies_as_integration(self):
        """File under tests/integration/ is classified as INTEGRATION."""
        self._create_file("tests/integration/test_api_flow.py")
        result = classify_file(os.path.join("tests", "integration", "test_api_flow.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["method"], "path_pattern")

    def test_api_path_classifies_as_integration(self):
        """File under tests/api/ is classified as INTEGRATION."""
        self._create_file("tests/api/test_endpoints.py")
        result = classify_file(os.path.join("tests", "api", "test_endpoints.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)

    def test_contract_path_classifies_as_integration(self):
        """File under tests/contract/ is INTEGRATION with CONTRACT sub-type."""
        self._create_file("tests/contract/test_schema.py")
        result = classify_file(os.path.join("tests", "contract", "test_schema.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["subtype"], SUBTYPE_CONTRACT)

    def test_unit_path_defaults_to_unit(self):
        """File under tests/unit/ doesn't match integration patterns — defaults to UNIT."""
        self._create_file("tests/unit/test_math.py")
        result = classify_file(os.path.join("tests", "unit", "test_math.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_UNIT)


class TestClassifyFileNamePatterns(unittest.TestCase):
    """AC1: Naming convention classification."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = {"test_layers": {
            "integration_path_patterns": [],
            "integration_name_patterns": [
                "*_contract_test.py",
                "*_pact_test.py",
                "*_api_test.py",
                "*_component_test.py",
                "test_*_contract.py",
                "test_*_pact.py",
                "test_*_api.py",
                "test_*_component.py"
            ],
            "custom_rules": {}
        }}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_contract_name_classifies_as_integration(self):
        """File named *_contract_test.py is INTEGRATION."""
        self._create_file("tests/user_contract_test.py")
        result = classify_file(os.path.join("tests", "user_contract_test.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["method"], "name_pattern")
        self.assertEqual(result["subtype"], SUBTYPE_CONTRACT)

    def test_pact_name_classifies_as_integration(self):
        """File named test_*_pact.py is INTEGRATION with PACT sub-type."""
        self._create_file("tests/test_auth_pact.py")
        result = classify_file(os.path.join("tests", "test_auth_pact.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["subtype"], SUBTYPE_PACT)

    def test_api_name_classifies_as_integration(self):
        """File named test_*_api.py is INTEGRATION with API sub-type."""
        self._create_file("tests/test_users_api.py")
        result = classify_file(os.path.join("tests", "test_users_api.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["subtype"], SUBTYPE_API)

    def test_component_name_classifies_as_integration(self):
        """File named *_component_test.py is INTEGRATION with COMPONENT sub-type."""
        self._create_file("tests/login_component_test.py")
        result = classify_file(os.path.join("tests", "login_component_test.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["subtype"], SUBTYPE_COMPONENT)


class TestClassifyFileMarkers(unittest.TestCase):
    """AC1: Marker/decorator classification."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = {"test_layers": {
            "integration_path_patterns": [],
            "integration_name_patterns": [],
            "custom_rules": {}
        }}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_pytest_marker_classifies_as_integration(self):
        """File with @pytest.mark.integration is classified as INTEGRATION."""
        source = '''import pytest

@pytest.mark.integration
class TestDatabase(unittest.TestCase):
    pass
'''
        self._create_file("tests/test_db.py", source)
        result = classify_file(os.path.join("tests", "test_db.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["method"], "marker")

    def test_class_layer_attribute_classifies_as_integration(self):
        """File with class-level layer = 'integration' is classified as INTEGRATION."""
        source = '''import unittest

class TestExternal(unittest.TestCase):
    layer = "integration"

    def test_something(self):
        pass
'''
        self._create_file("tests/test_external.py", source)
        result = classify_file(os.path.join("tests", "test_external.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["method"], "marker")

    def test_no_marker_defaults_to_unit(self):
        """File without integration markers defaults to UNIT."""
        source = '''import unittest

class TestPure(unittest.TestCase):
    def test_add(self):
        self.assertEqual(1 + 1, 2)
'''
        self._create_file("tests/test_pure.py", source)
        result = classify_file(os.path.join("tests", "test_pure.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_UNIT)
        self.assertEqual(result["method"], "default")


class TestClassifyFileCustomRules(unittest.TestCase):
    """AC2: Custom rules take precedence over defaults."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_custom_rule_overrides_default(self):
        """Custom rule classifies a file that would default to UNIT as INTEGRATION."""
        config = {"test_layers": {
            "integration_path_patterns": [],
            "integration_name_patterns": [],
            "custom_rules": {
                "test_output_contracts.py": "INTEGRATION"
            }
        }}
        self._create_file("tests/test_output_contracts.py")
        result = classify_file(os.path.join("tests", "test_output_contracts.py"), config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["method"], "custom_rule")

    def test_custom_rule_with_subtype(self):
        """Custom rule with explicit subtype."""
        config = {"test_layers": {
            "integration_path_patterns": [],
            "integration_name_patterns": [],
            "custom_rules": {
                "test_output_contracts.py": {"layer": "INTEGRATION", "subtype": "CONTRACT"}
            }
        }}
        self._create_file("tests/test_output_contracts.py")
        result = classify_file(os.path.join("tests", "test_output_contracts.py"), config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertEqual(result["subtype"], SUBTYPE_CONTRACT)
        self.assertEqual(result["method"], "custom_rule")

    def test_custom_rule_takes_precedence_over_path(self):
        """Custom UNIT rule overrides path-based INTEGRATION."""
        config = {"test_layers": {
            "integration_path_patterns": ["tests/integration/"],
            "integration_name_patterns": [],
            "custom_rules": {
                "tests/integration/test_special.py": "UNIT"
            }
        }}
        self._create_file("tests/integration/test_special.py")
        result = classify_file(os.path.join("tests", "integration", "test_special.py"), config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_UNIT)
        self.assertEqual(result["method"], "custom_rule")


class TestClassifyFileSubTypes(unittest.TestCase):
    """AC4: Integration sub-type detection."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = {"test_layers": {
            "integration_path_patterns": [
                "tests/integration/",
                "tests/api/",
                "tests/contract/",
                "tests/pact/",
                "tests/component/"
            ],
            "integration_name_patterns": [],
            "custom_rules": {}
        }}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_api_subtype_from_path(self):
        """API sub-type detected from path."""
        self._create_file("tests/api/test_users.py")
        result = classify_file(os.path.join("tests", "api", "test_users.py"), self.config, self.test_dir)
        self.assertEqual(result["subtype"], SUBTYPE_API)

    def test_pact_subtype_from_path(self):
        """PACT sub-type detected from path."""
        self._create_file("tests/pact/test_provider.py")
        result = classify_file(os.path.join("tests", "pact", "test_provider.py"), self.config, self.test_dir)
        self.assertEqual(result["subtype"], SUBTYPE_PACT)

    def test_component_subtype_from_path(self):
        """COMPONENT sub-type detected from path."""
        self._create_file("tests/component/test_widget.py")
        result = classify_file(os.path.join("tests", "component", "test_widget.py"), self.config, self.test_dir)
        self.assertEqual(result["subtype"], SUBTYPE_COMPONENT)

    def test_no_subtype_for_generic_integration(self):
        """Generic integration path gets no sub-type."""
        self._create_file("tests/integration/test_flow.py")
        result = classify_file(os.path.join("tests", "integration", "test_flow.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_INTEGRATION)
        self.assertIsNone(result["subtype"])

    def test_unit_files_have_no_subtype(self):
        """UNIT files never have a sub-type."""
        self._create_file("tests/test_math.py")
        result = classify_file(os.path.join("tests", "test_math.py"), self.config, self.test_dir)
        self.assertEqual(result["layer"], LAYER_UNIT)
        self.assertIsNone(result["subtype"])


class TestClassifyAll(unittest.TestCase):
    """AC3: Full project classification and layer overview."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = {"test_layers": {
            "integration_path_patterns": ["tests/integration/", "tests/api/"],
            "integration_name_patterns": ["*_contract_test.py"],
            "custom_rules": {}
        }}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_classify_all_returns_all_files(self):
        """classify_all returns a classification for every test file."""
        self._create_file("tests/test_a.py")
        self._create_file("tests/test_b.py")
        self._create_file("tests/integration/test_c.py")
        results = classify_all(self.test_dir, self.config)
        self.assertEqual(len(results), 3)

    def test_classify_all_groups_correctly(self):
        """classify_all assigns correct layers to mixed files."""
        self._create_file("tests/test_unit.py")
        self._create_file("tests/integration/test_int.py")
        self._create_file("tests/api/test_api.py")
        results = classify_all(self.test_dir, self.config)
        layers = {r["file"]: r["layer"] for r in results}
        self.assertEqual(layers[os.path.join("tests", "test_unit.py")], LAYER_UNIT)
        self.assertEqual(layers[os.path.join("tests", "integration", "test_int.py")], LAYER_INTEGRATION)
        self.assertEqual(layers[os.path.join("tests", "api", "test_api.py")], LAYER_INTEGRATION)

    def test_classify_all_empty_project(self):
        """classify_all returns empty list when no test files exist."""
        results = classify_all(self.test_dir, self.config)
        self.assertEqual(results, [])


class TestPersistAndLoadLayers(unittest.TestCase):
    """AC1: Classification persistence for downstream use."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_persist_creates_layers_json(self):
        """persist_layers writes .lisa/layers.json."""
        classifications = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        path = persist_layers(self.test_dir, classifications)
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["layer"], "UNIT")

    def test_load_returns_persisted_data(self):
        """load_layers reads back what persist_layers wrote."""
        classifications = [
            {"file": "tests/test_a.py", "layer": "UNIT", "subtype": None, "method": "default"},
            {"file": "tests/api/test_b.py", "layer": "INTEGRATION", "subtype": "API", "method": "path_pattern"},
        ]
        persist_layers(self.test_dir, classifications)
        loaded = load_layers(self.test_dir)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[1]["subtype"], "API")

    def test_load_returns_none_when_missing(self):
        """load_layers returns None when no layers.json exists."""
        result = load_layers(self.test_dir)
        self.assertIsNone(result)

    def test_persist_creates_lisa_dir_if_missing(self):
        """persist_layers creates .lisa/ directory if it doesn't exist."""
        fresh_dir = tempfile.mkdtemp()
        try:
            classifications = [{"file": "test_x.py", "layer": "UNIT", "subtype": None, "method": "default"}]
            path = persist_layers(fresh_dir, classifications)
            self.assertTrue(os.path.exists(path))
        finally:
            shutil.rmtree(fresh_dir)


class TestClassifyCommand(unittest.TestCase):
    """AC3: The lisa classify command output."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        self.original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_classify_all_output_includes_required_fields(self):
        """lisa classify --all output includes UNIT count, INTEGRATION count, Total."""
        from unittest.mock import patch
        from lisa.commands import classify

        self._create_file("tests/test_a.py")
        self._create_file("tests/integration/test_b.py")

        mock_config = {
            "test_layers": {
                "integration_path_patterns": ["tests/integration/"],
                "integration_name_patterns": [],
                "custom_rules": {}
            }
        }

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.ConfigManager') as MockConfig, \
             patch('lisa.commands.print_with_status') as mock_print:
            MockConfig.return_value.load.return_value = mock_config
            result = classify(["--all"])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("UNIT:", all_output)
        self.assertIn("INTEGRATION:", all_output)
        self.assertIn("Total:", all_output)

    def test_classify_single_file_output(self):
        """lisa classify <file> outputs file, layer, and method."""
        from unittest.mock import patch
        from lisa.commands import classify

        self._create_file("tests/test_foo.py")

        mock_config = {
            "test_layers": {
                "integration_path_patterns": [],
                "integration_name_patterns": [],
                "custom_rules": {}
            }
        }

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.ConfigManager') as MockConfig, \
             patch('lisa.commands.print_with_status') as mock_print:
            MockConfig.return_value.load.return_value = mock_config
            result = classify([os.path.join("tests", "test_foo.py")])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("File:", all_output)
        self.assertIn("Layer: UNIT", all_output)
        self.assertIn("Method:", all_output)

    def test_classify_missing_file_returns_error(self):
        """lisa classify <nonexistent> returns exit code 1."""
        from unittest.mock import patch
        from lisa.commands import classify

        with patch('lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('lisa.commands.ConfigManager') as MockConfig, \
             patch('lisa.commands.print_with_status'):
            MockConfig.return_value.load.return_value = {"test_layers": {}}
            result = classify(["tests/nonexistent.py"])

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
