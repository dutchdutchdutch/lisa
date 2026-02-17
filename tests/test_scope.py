"""Tests for scope derivation (Story 7.2).

Covers: derive_modified_files_from_git, compute_dependency_cone,
find_in_scope_tests, persist/load/clear scope, and the CLI scope command.
"""
import unittest
import os
import json
import tempfile
import shutil
import subprocess

from scripts.lisa.scope import (
    derive_modified_files_from_git,
    compute_dependency_cone,
    find_in_scope_tests,
    derive_scope,
    persist_scope,
    load_scope,
    clear_scope,
)


class TestComputeDependencyCone(unittest.TestCase):
    """AC1: Dependency cone computation from modified files."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_single_file_no_dependents(self):
        """Modified file with no importers has a cone of just itself."""
        self._create_file("src/utils.py", "def helper(): pass")
        cone = compute_dependency_cone(["src/utils.py"], self.test_dir)
        self.assertEqual(cone, ["src/utils.py"])

    def test_single_file_with_dependents(self):
        """Modified file with importers includes both in the cone."""
        self._create_file("src/utils.py", "def helper(): pass")
        self._create_file("src/main.py", "from src.utils import helper")
        cone = compute_dependency_cone(["src/utils.py"], self.test_dir)
        self.assertIn("src/utils.py", cone)
        self.assertIn(os.path.join("src", "main.py"), cone)

    def test_multiple_modified_files(self):
        """Multiple modified files merge their dependency cones."""
        self._create_file("src/a.py", "def a(): pass")
        self._create_file("src/b.py", "def b(): pass")
        self._create_file("src/c.py", "from src.a import a\nfrom src.b import b")
        cone = compute_dependency_cone(["src/a.py", "src/b.py"], self.test_dir)
        self.assertIn("src/a.py", cone)
        self.assertIn("src/b.py", cone)
        self.assertIn(os.path.join("src", "c.py"), cone)

    def test_empty_modified_files(self):
        """Empty list returns empty cone."""
        cone = compute_dependency_cone([], self.test_dir)
        self.assertEqual(cone, [])

    def test_deduplicates_cone(self):
        """Files appearing in multiple dependency cones are deduplicated."""
        self._create_file("src/a.py", "def a(): pass")
        self._create_file("src/b.py", "from src.a import a")
        # b depends on a; modifying both should not duplicate b
        cone = compute_dependency_cone(["src/a.py", "src/b.py"], self.test_dir)
        self.assertEqual(len(cone), len(set(cone)))


class TestFindInScopeTests(unittest.TestCase):
    """AC1/AC2: Reverse mapping from dependency cone to test files by layer."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_finds_unit_test_importing_module(self):
        """A unit test that imports a cone module is in-scope."""
        self._create_file("src/utils.py", "def helper(): pass")
        self._create_file("tests/test_utils.py", "from src.utils import helper")
        classifications = [
            {"file": os.path.join("tests", "test_utils.py"), "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        cone = ["src/utils.py"]
        result = find_in_scope_tests(cone, classifications, self.test_dir)
        self.assertIn(os.path.join("tests", "test_utils.py"), result["UNIT"])

    def test_finds_integration_test_importing_module(self):
        """An integration test that imports a cone module is in-scope."""
        self._create_file("src/api.py", "def endpoint(): pass")
        self._create_file("tests/integration/test_api.py", "from src.api import endpoint")
        classifications = [
            {"file": os.path.join("tests", "integration", "test_api.py"), "layer": "INTEGRATION", "subtype": "API", "method": "path_pattern"},
        ]
        cone = ["src/api.py"]
        result = find_in_scope_tests(cone, classifications, self.test_dir)
        self.assertIn(os.path.join("tests", "integration", "test_api.py"), result["INTEGRATION"])

    def test_excludes_test_not_importing_cone(self):
        """A test that does not import any cone module is out-of-scope."""
        self._create_file("src/utils.py", "def helper(): pass")
        self._create_file("src/other.py", "def other(): pass")
        self._create_file("tests/test_other.py", "from src.other import other")
        classifications = [
            {"file": os.path.join("tests", "test_other.py"), "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        cone = ["src/utils.py"]  # other.py is NOT in the cone
        result = find_in_scope_tests(cone, classifications, self.test_dir)
        self.assertEqual(result["UNIT"], [])
        self.assertEqual(result["INTEGRATION"], [])

    def test_groups_by_layer(self):
        """Result has UNIT and INTEGRATION keys."""
        result = find_in_scope_tests([], [], self.test_dir)
        self.assertIn("UNIT", result)
        self.assertIn("INTEGRATION", result)

    def test_empty_classifications(self):
        """No classifications returns empty groups."""
        result = find_in_scope_tests(["src/foo.py"], [], self.test_dir)
        self.assertEqual(result["UNIT"], [])
        self.assertEqual(result["INTEGRATION"], [])


class TestPersistLoadClearScope(unittest.TestCase):
    """AC3: Scope persistence, loading, and clearing."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_persist_creates_scope_json(self):
        """persist_scope writes .lisa/scope.json."""
        scope_data = {
            "modified_files": ["src/foo.py"],
            "dependency_cone": ["src/foo.py", "src/bar.py"],
            "in_scope_tests": {"UNIT": ["tests/test_foo.py"], "INTEGRATION": []},
            "source": "explicit",
        }
        path = persist_scope(self.test_dir, scope_data)
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["modified_files"], ["src/foo.py"])

    def test_load_returns_persisted_data(self):
        """load_scope reads back what persist_scope wrote."""
        scope_data = {
            "modified_files": ["src/a.py"],
            "dependency_cone": ["src/a.py"],
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "source": "git_diff",
        }
        persist_scope(self.test_dir, scope_data)
        loaded = load_scope(self.test_dir)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["source"], "git_diff")

    def test_load_returns_none_when_missing(self):
        """load_scope returns None when no scope.json exists."""
        result = load_scope(self.test_dir)
        self.assertIsNone(result)

    def test_clear_removes_scope(self):
        """clear_scope removes .lisa/scope.json."""
        scope_data = {
            "modified_files": ["x.py"],
            "dependency_cone": ["x.py"],
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "source": "explicit",
        }
        persist_scope(self.test_dir, scope_data)
        cleared = clear_scope(self.test_dir)
        self.assertTrue(cleared)
        self.assertIsNone(load_scope(self.test_dir))

    def test_clear_returns_false_when_no_scope(self):
        """clear_scope returns False if no scope exists."""
        cleared = clear_scope(self.test_dir)
        self.assertFalse(cleared)

    def test_persist_creates_lisa_dir_if_missing(self):
        """persist_scope creates .lisa/ directory if it doesn't exist."""
        fresh_dir = tempfile.mkdtemp()
        try:
            scope_data = {
                "modified_files": [],
                "dependency_cone": [],
                "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
                "source": "explicit",
            }
            path = persist_scope(fresh_dir, scope_data)
            self.assertTrue(os.path.exists(path))
        finally:
            shutil.rmtree(fresh_dir)


class TestDeriveModifiedFilesFromGit(unittest.TestCase):
    """AC4: Version control integration — deriving modified files from git diff."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.test_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def _git(self, *cmd_args):
        subprocess.run(["git"] + list(cmd_args), cwd=self.test_dir, capture_output=True)

    def test_detects_modified_files(self):
        """Modified files on current branch are detected vs base branch."""
        # Create initial commit on main
        self._create_file("src/a.py", "# original")
        self._git("add", ".")
        self._git("commit", "-m", "initial")
        self._git("branch", "-M", "main")

        # Create feature branch with changes
        self._git("checkout", "-b", "feature")
        self._create_file("src/a.py", "# modified")
        self._create_file("src/b.py", "# new file")
        self._git("add", ".")
        self._git("commit", "-m", "feature changes")

        files = derive_modified_files_from_git(self.test_dir, base_branch="main")
        self.assertIn(os.path.join("src", "a.py"), files)
        self.assertIn(os.path.join("src", "b.py"), files)

    def test_filters_to_python_source_files(self):
        """Only .py files are included (not .md, .json, etc)."""
        self._create_file("README.md", "# readme")
        self._git("add", ".")
        self._git("commit", "-m", "initial")
        self._git("branch", "-M", "main")

        self._git("checkout", "-b", "feature")
        self._create_file("README.md", "# updated")
        self._create_file("src/new.py", "# code")
        self._create_file("data.json", "{}")
        self._git("add", ".")
        self._git("commit", "-m", "mixed changes")

        files = derive_modified_files_from_git(self.test_dir, base_branch="main")
        self.assertIn(os.path.join("src", "new.py"), files)
        self.assertNotIn("README.md", files)
        self.assertNotIn("data.json", files)

    def test_returns_empty_list_when_no_changes(self):
        """Returns empty list when branch has no changes vs base."""
        self._create_file("src/a.py", "# code")
        self._git("add", ".")
        self._git("commit", "-m", "initial")
        self._git("branch", "-M", "main")

        self._git("checkout", "-b", "feature")
        # No changes

        files = derive_modified_files_from_git(self.test_dir, base_branch="main")
        self.assertEqual(files, [])

    def test_excludes_test_files(self):
        """Test files are excluded from modified files (they are targets, not inputs)."""
        self._create_file("src/code.py", "# code")
        self._git("add", ".")
        self._git("commit", "-m", "initial")
        self._git("branch", "-M", "main")

        self._git("checkout", "-b", "feature")
        self._create_file("src/code.py", "# modified code")
        self._create_file("tests/test_code.py", "# new test")
        self._git("add", ".")
        self._git("commit", "-m", "code and test")

        files = derive_modified_files_from_git(self.test_dir, base_branch="main")
        self.assertIn(os.path.join("src", "code.py"), files)
        # test files should be excluded
        for f in files:
            basename = os.path.basename(f)
            self.assertFalse(
                basename.startswith("test_") or basename.endswith("_test.py"),
                f"Test file should be excluded: {f}"
            )


class TestDeriveScope(unittest.TestCase):
    """AC1/AC2: Full scope derivation pipeline (explicit file list)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_derive_scope_with_explicit_files(self):
        """derive_scope from explicit file list produces correct scope data."""
        self._create_file("src/utils.py", "def helper(): pass")
        self._create_file("tests/test_utils.py", "from src.utils import helper")

        classifications = [
            {"file": os.path.join("tests", "test_utils.py"), "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        # Persist classifications so derive_scope can load them
        layers_path = os.path.join(self.test_dir, ".lisa", "layers.json")
        with open(layers_path, "w") as f:
            json.dump(classifications, f)

        scope = derive_scope(
            project_root=self.test_dir,
            modified_files=["src/utils.py"],
        )

        self.assertIn("src/utils.py", scope["modified_files"])
        self.assertIn("src/utils.py", scope["dependency_cone"])
        self.assertIn(os.path.join("tests", "test_utils.py"), scope["in_scope_tests"]["UNIT"])
        self.assertEqual(scope["source"], "explicit")

    def test_derive_scope_returns_none_without_layers(self):
        """derive_scope returns None if layers.json is missing."""
        self._create_file("src/utils.py", "def helper(): pass")
        scope = derive_scope(
            project_root=self.test_dir,
            modified_files=["src/utils.py"],
        )
        self.assertIsNone(scope)


class TestScopeCommand(unittest.TestCase):
    """AC2/AC3: The lisa scope CLI command."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, rel_path, content=""):
        abs_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)

    def test_scope_clear_removes_scope(self):
        """lisa scope --clear removes the scope file."""
        from unittest.mock import patch
        from scripts.lisa.commands import scope_cmd

        # Create a scope file
        scope_path = os.path.join(self.test_dir, ".lisa", "scope.json")
        with open(scope_path, "w") as f:
            json.dump({"modified_files": []}, f)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status'):
            result = scope_cmd(["--clear"])

        self.assertEqual(result, 0)
        self.assertFalse(os.path.exists(scope_path))

    def test_scope_show_displays_current_scope(self):
        """lisa scope (no args) shows current scope if set."""
        from unittest.mock import patch
        from scripts.lisa.commands import scope_cmd

        scope_data = {
            "modified_files": ["src/a.py"],
            "dependency_cone": ["src/a.py", "src/b.py"],
            "in_scope_tests": {"UNIT": ["tests/test_a.py"], "INTEGRATION": []},
            "source": "explicit",
        }
        scope_path = os.path.join(self.test_dir, ".lisa", "scope.json")
        with open(scope_path, "w") as f:
            json.dump(scope_data, f)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = scope_cmd([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("src/a.py", all_output)
        self.assertIn("UNIT", all_output)

    def test_scope_show_warns_when_no_scope(self):
        """lisa scope (no args) warns when no scope is set."""
        from unittest.mock import patch
        from scripts.lisa.commands import scope_cmd

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = scope_cmd([])

        self.assertEqual(result, 0)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("No scope", all_output)

    def test_scope_with_explicit_files(self):
        """lisa scope file1.py file2.py sets scope from explicit files."""
        from unittest.mock import patch
        from scripts.lisa.commands import scope_cmd

        self._create_file("src/a.py", "def a(): pass")
        self._create_file("tests/test_a.py", "from src.a import a")

        classifications = [
            {"file": os.path.join("tests", "test_a.py"), "layer": "UNIT", "subtype": None, "method": "default"},
        ]
        layers_path = os.path.join(self.test_dir, ".lisa", "layers.json")
        with open(layers_path, "w") as f:
            json.dump(classifications, f)

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.ConfigManager') as MockConfig, \
             patch('scripts.lisa.commands.print_with_status'):
            MockConfig.return_value.load.return_value = {"test_layers": {}}
            result = scope_cmd(["src/a.py"])

        self.assertEqual(result, 0)
        # Verify scope was persisted
        loaded = load_scope(self.test_dir)
        self.assertIsNotNone(loaded)
        self.assertIn("src/a.py", loaded["modified_files"])

    def test_scope_with_git_flag(self):
        """lisa scope --git derives from version control."""
        from unittest.mock import patch
        from scripts.lisa.commands import scope_cmd

        mock_modified = ["src/x.py"]
        mock_scope = {
            "modified_files": ["src/x.py"],
            "dependency_cone": ["src/x.py"],
            "in_scope_tests": {"UNIT": [], "INTEGRATION": []},
            "source": "git_diff",
        }

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.ConfigManager') as MockConfig, \
             patch('scripts.lisa.commands.derive_modified_files_from_git', return_value=mock_modified), \
             patch('scripts.lisa.commands.derive_scope', return_value=mock_scope), \
             patch('scripts.lisa.commands.persist_scope'), \
             patch('scripts.lisa.commands.print_with_status'):
            MockConfig.return_value.load.return_value = {}
            result = scope_cmd(["--git"])

        self.assertEqual(result, 0)

    def test_scope_git_warns_no_modified_files(self):
        """lisa scope --git warns when no modified files found."""
        from unittest.mock import patch
        from scripts.lisa.commands import scope_cmd

        with patch('scripts.lisa.commands.find_project_root', return_value=self.test_dir), \
             patch('scripts.lisa.commands.ConfigManager') as MockConfig, \
             patch('scripts.lisa.commands.derive_modified_files_from_git', return_value=[]), \
             patch('scripts.lisa.commands.print_with_status') as mock_print:
            MockConfig.return_value.load.return_value = {}
            result = scope_cmd(["--git"])

        self.assertEqual(result, 1)
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("No modified", all_output)


if __name__ == "__main__":
    unittest.main()
