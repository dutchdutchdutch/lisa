import unittest
import os
import shutil
import tempfile
import json
from unittest.mock import patch
from scripts.lisa.state import StateManager

class TestStateManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Create .lisa dir
        os.makedirs(".lisa", exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_increment_turn(self):
        """Should increment turn_count in state file."""
        manager = StateManager(project_root=self.test_dir)

        # Initial State: 0 or undefined
        self.assertEqual(manager.load().get("turn_count", 0), 0)

        # Increment
        new_count = manager.increment_turn()
        self.assertEqual(new_count, 1)

        # Verify persistence
        with open(os.path.join(self.test_dir, ".lisa/state.json"), "r") as f:
            data = json.load(f)
            self.assertEqual(data["turn_count"], 1)

    def test_reset_turn(self):
        """Should reset turn_count to 0."""
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 15)

        manager.reset_turn()
        self.assertEqual(manager.load()["turn_count"], 0)


class TestStatePersistenceFallback(unittest.TestCase):
    """Story 5.8 Criteria 1 & 2: Zero-Config Persistence and Graceful Degradation."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        StateManager._fallback_warned.clear()

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_primary_path_used_when_writable(self):
        """Criteria 1: Uses .lisa/state.json when writable."""
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        manager = StateManager(project_root=self.test_dir)

        expected = os.path.join(self.test_dir, ".lisa", "state.json")
        self.assertEqual(manager.state_file, expected)
        self.assertFalse(manager.using_fallback)

    def test_fallback_when_primary_not_writable(self):
        """Criteria 2: Falls back to temp dir with visible warning when .lisa/ is not writable."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(lisa_dir, exist_ok=True)
        os.chmod(lisa_dir, 0o444)

        try:
            manager = StateManager(project_root=self.test_dir)

            self.assertTrue(manager.using_fallback)
            self.assertIn(tempfile.gettempdir(), manager.state_file)

            # Warning emitted via warn_if_fallback on stdout (not hidden in stderr)
            with patch('builtins.print') as mock_print:
                manager.warn_if_fallback()
            mock_print.assert_called()
            warning_text = mock_print.call_args[0][0]
            self.assertIn("not writable", warning_text.lower())
        finally:
            os.chmod(lisa_dir, 0o755)

    def test_fallback_state_persists_across_instances(self):
        """Criteria 1: State persists across command invocations even in fallback."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(lisa_dir, exist_ok=True)
        os.chmod(lisa_dir, 0o444)

        try:
            manager1 = StateManager(project_root=self.test_dir)
            manager1.update("turn_count", 7)

            manager2 = StateManager(project_root=self.test_dir)
            state = manager2.load()
            self.assertEqual(state["turn_count"], 7)
        finally:
            os.chmod(lisa_dir, 0o755)

    def test_fallback_warning_suggests_fix_command(self):
        """Criteria 2: Warning suggests `lisa init --fix`."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(lisa_dir, exist_ok=True)
        os.chmod(lisa_dir, 0o444)

        try:
            manager = StateManager(project_root=self.test_dir)

            with patch('builtins.print') as mock_print:
                manager.warn_if_fallback()

            warning_text = str(mock_print.call_args[0][0])
            self.assertIn("lisa init --fix", warning_text)
        finally:
            os.chmod(lisa_dir, 0o755)

    def test_warn_if_fallback_fires_once_per_process(self):
        """warn_if_fallback() only emits the warning once per project root."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(lisa_dir, exist_ok=True)
        os.chmod(lisa_dir, 0o444)

        try:
            manager = StateManager(project_root=self.test_dir)

            with patch('builtins.print') as mock_print:
                manager.warn_if_fallback()
                manager.warn_if_fallback()  # Second call should be no-op

            # print called exactly once despite two warn_if_fallback calls
            self.assertEqual(mock_print.call_count, 1)
        finally:
            os.chmod(lisa_dir, 0o755)


class TestStateDiagnose(unittest.TestCase):
    """Story 5.8 Criteria 3: diagnose() health checks."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_healthy_when_primary_writable(self):
        """diagnose() returns healthy when primary path works."""
        manager = StateManager(project_root=self.test_dir)
        result = manager.diagnose()

        self.assertTrue(result["healthy"])
        self.assertIsNone(result["issue"])
        self.assertFalse(result["using_fallback"])

    def test_unhealthy_when_using_fallback(self):
        """diagnose() reports unhealthy when on fallback storage."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.chmod(lisa_dir, 0o444)

        try:
            manager = StateManager(project_root=self.test_dir)
            result = manager.diagnose()

            self.assertFalse(result["healthy"])
            self.assertTrue(result["using_fallback"])
            self.assertIn("temporary directory", result["issue"])
        finally:
            os.chmod(lisa_dir, 0o755)


class TestStateRepair(unittest.TestCase):
    """Story 5.8 Criteria 3: Self-Healing via repair()."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_repair_creates_lisa_dir_and_switches_to_primary(self):
        """repair() creates .lisa/ and switches from fallback to primary."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(lisa_dir, exist_ok=True)
        os.chmod(lisa_dir, 0o444)

        try:
            manager = StateManager(project_root=self.test_dir)
            self.assertTrue(manager.using_fallback)

            # Write some state to fallback
            manager.update("turn_count", 5)
        finally:
            # Now "fix" the permissions (simulating what repair would do)
            os.chmod(lisa_dir, 0o755)

        # Repair should succeed now that directory is writable again
        success, message = manager.repair()
        self.assertTrue(success)
        self.assertFalse(manager.using_fallback)
        self.assertIn(".lisa/state.json", manager.state_file)

    def test_repair_migrates_state_from_fallback(self):
        """repair() migrates existing state from fallback to primary."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(lisa_dir, exist_ok=True)
        os.chmod(lisa_dir, 0o444)

        try:
            manager = StateManager(project_root=self.test_dir)
            manager.update("turn_count", 42)
        finally:
            os.chmod(lisa_dir, 0o755)

        success, _ = manager.repair()
        self.assertTrue(success)

        # Verify state was migrated
        state = manager.load()
        self.assertEqual(state["turn_count"], 42)

    def test_repair_cleans_up_fallback_files(self):
        """repair() removes orphaned fallback files after migration."""
        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.makedirs(lisa_dir, exist_ok=True)
        os.chmod(lisa_dir, 0o444)

        try:
            manager = StateManager(project_root=self.test_dir)
            fallback_file = manager.state_file
            fallback_dir = os.path.dirname(fallback_file)
            manager.update("turn_count", 1)
        finally:
            os.chmod(lisa_dir, 0o755)

        self.assertTrue(os.path.exists(fallback_file))

        success, _ = manager.repair()
        self.assertTrue(success)

        # Fallback file and directory should be cleaned up
        self.assertFalse(os.path.exists(fallback_file))
        self.assertFalse(os.path.exists(fallback_dir))

    def test_repair_fails_without_project_root(self):
        """repair() fails gracefully if no project_root is set."""
        manager = StateManager(state_file=os.path.join(self.test_dir, "state.json"))
        success, message = manager.repair()

        self.assertFalse(success)
        self.assertIn("no project root", message.lower())

    def test_repair_on_already_healthy_system(self):
        """repair() succeeds on an already-healthy system (idempotent)."""
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)
        manager = StateManager(project_root=self.test_dir)

        success, message = manager.repair()
        self.assertTrue(success)
        self.assertFalse(manager.using_fallback)


class TestTurnCounterAccuracy(unittest.TestCase):
    """Story 5.8 Criteria 4: Turn counter reflects updates in health reports."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_turn_count_persists_and_reflects_in_load(self):
        """Setting turn count via update persists across load calls."""
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 12)

        # New manager instance, same project
        manager2 = StateManager(project_root=self.test_dir)
        state = manager2.load()
        self.assertEqual(state["turn_count"], 12)

    def test_turn_counter_survives_multiple_increments(self):
        """Increments accumulate correctly across calls."""
        manager = StateManager(project_root=self.test_dir)

        for i in range(1, 13):
            result = manager.increment_turn()
            self.assertEqual(result, i)

        # Verify final state via fresh instance
        manager2 = StateManager(project_root=self.test_dir)
        self.assertEqual(manager2.load()["turn_count"], 12)

    @patch('scripts.lisa.commands.scan_workspace')
    @patch('scripts.lisa.commands.find_project_root')
    @patch('scripts.lisa.commands.ConfigManager')
    def test_context_health_reflects_updated_turn(self, MockConfig, mock_find_root, mock_scan):
        """Criteria 4: `lisa context health` reflects the turn count set by `lisa turns`."""
        from scripts.lisa.commands import context_health

        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 20)
        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        # Set turn to 12 (Goldfish Threshold)
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 12)

        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            context_health([])

        # Turn count 12 should show amber (warning threshold)
        mock_print.assert_any_call("Turn Count:      12", status_icon="🟡")
        # Goldfish Threshold warning text must fire (AC4)
        mock_print.assert_any_call("WARNING: Approaching Turn Limit (12-20).", status_icon="🟡")

    @patch('scripts.lisa.commands.scan_workspace')
    @patch('scripts.lisa.commands.find_project_root')
    @patch('scripts.lisa.commands.ConfigManager')
    def test_context_health_red_at_turn_limit(self, MockConfig, mock_find_root, mock_scan):
        """Criteria 4: Turn count > 20 (turn_limit) triggers red status in health report."""
        from scripts.lisa.commands import context_health

        mock_find_root.return_value = self.test_dir
        mock_scan.return_value = (5000, 20)
        mock_config = {"context_limit": 160000, "turn_warning_threshold": 12, "turn_limit": 20}
        MockConfig.return_value.load.return_value = mock_config
        MockConfig.return_value.get.side_effect = mock_config.get

        # Set turn to 21 (exceeds limit of 20)
        manager = StateManager(project_root=self.test_dir)
        manager.update("turn_count", 21)

        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            context_health([])

        # Turn count 21 should show red (exceeded limit)
        mock_print.assert_any_call("Turn Count:      21", status_icon="🔴")
        # Critical warning text must fire
        mock_print.assert_any_call("CRITICAL: Turn Limit Exceeded (>20).", status_icon="🔴")


class TestInitFix(unittest.TestCase):
    """Story 5.8 Criteria 3: `lisa init --fix` self-healing command."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs(os.path.join(self.test_dir, ".lisa"), exist_ok=True)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    @patch('scripts.lisa.commands.find_project_root')
    def test_init_fix_healthy_system(self, mock_find_root):
        """--fix on a healthy system reports no repairs needed."""
        from scripts.lisa.commands import init_session

        mock_find_root.return_value = self.test_dir

        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = init_session(["--fix"])

        self.assertEqual(result, 0)
        mock_print.assert_any_call("State storage is healthy. No repairs needed.", status_icon="🟢")

    @patch('scripts.lisa.commands.find_project_root')
    def test_init_fix_repairs_broken_storage(self, mock_find_root):
        """--fix detects and repairs a broken state storage."""
        from scripts.lisa.commands import init_session

        mock_find_root.return_value = self.test_dir

        lisa_dir = os.path.join(self.test_dir, ".lisa")
        os.chmod(lisa_dir, 0o444)

        try:
            # Create a fallback StateManager (simulates broken state)
            fallback_sm = StateManager(project_root=self.test_dir)
            self.assertTrue(fallback_sm.using_fallback)
            fallback_sm.update("turn_count", 99)

            # Fix permissions (simulates user/admin resolving the underlying issue)
            os.chmod(lisa_dir, 0o755)

            # Inject the fallback StateManager into _init_fix so it exercises
            # the unhealthy → repair → verify path
            with patch('scripts.lisa.commands.StateManager', return_value=fallback_sm):
                with patch('scripts.lisa.commands.print_with_status') as mock_print:
                    result = init_session(["--fix"])
        finally:
            try:
                os.chmod(lisa_dir, 0o755)
            except OSError:
                pass

        self.assertEqual(result, 0)
        # Assert the unhealthy diagnosis path was taken
        call_texts = [str(c) for c in mock_print.call_args_list]
        self.assertTrue(any("Issue detected" in t for t in call_texts))
        # Assert repair succeeded
        mock_print.assert_any_call("Verified: state is writable.", status_icon="🟢")

    @patch('scripts.lisa.commands.find_project_root')
    def test_init_fix_routes_correctly(self, mock_find_root):
        """init_session with --fix calls _init_fix, without it does normal init."""
        from scripts.lisa.commands import init_session

        mock_find_root.return_value = self.test_dir

        # With --fix: should call diagnose path (returns 0 on healthy)
        with patch('scripts.lisa.commands.print_with_status'):
            result = init_session(["--fix"])
        self.assertEqual(result, 0)

        # Without --fix: should try to load todo.md (which doesn't exist)
        with patch('scripts.lisa.commands.print_with_status') as mock_print:
            result = init_session([])
        self.assertEqual(result, 1)
