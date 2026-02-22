import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from lisa.commands import _init_setup

class TestHookActivation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('lisa.commands.status_cmd')
    def test_init_setup_copies_bridge(self, mock_status):
        """Should copy lisa.sh to .lisa/lisa.sh."""
        mock_status.return_value = 0
        _init_setup(self.test_dir)
        
        bridge_path = os.path.join(self.test_dir, ".lisa", "lisa.sh")
        self.assertTrue(os.path.exists(bridge_path))
        # Check if executable
        self.assertTrue(os.access(bridge_path, os.X_OK))

    @patch('lisa.commands.status_cmd')
    def test_init_setup_installs_git_hooks(self, mock_status):
        """Should install git hooks if .git directory exists."""
        mock_status.return_value = 0
        
        # Mock .git/hooks directory
        os.makedirs(os.path.join(self.test_dir, ".git", "hooks"))
        
        _init_setup(self.test_dir)
        
        post_commit = os.path.join(self.test_dir, ".git", "hooks", "post-commit")
        pre_push = os.path.join(self.test_dir, ".git", "hooks", "pre-push")
        
        self.assertTrue(os.path.exists(post_commit))
        self.assertTrue(os.path.exists(pre_push))
        
        with open(post_commit, "r") as f:
            content = f.read()
            self.assertIn(".lisa/lisa.sh hooks story-in-dev", content)
            
        with open(pre_push, "r") as f:
            content = f.read()
            self.assertIn(".lisa/lisa.sh hooks story-test", content)

    @patch('lisa.commands.status_cmd')
    def test_git_hook_idempotency(self, mock_status):
        """Should not duplicate handover in existing hooks."""
        mock_status.return_value = 0
        hooks_dir = os.path.join(self.test_dir, ".git", "hooks")
        os.makedirs(hooks_dir)
        
        hook_path = os.path.join(hooks_dir, "post-commit")
        initial_content = "#!/bin/bash\necho 'hello'\n"
        with open(hook_path, "w") as f:
            f.write(initial_content)
            
        # First run
        _init_setup(self.test_dir)
        with open(hook_path, "r") as f:
            content1 = f.read()
            self.assertIn(".lisa/lisa.sh hooks story-in-dev", content1)
            self.assertEqual(content1.count(".lisa/lisa.sh hooks story-in-dev"), 1)
            
        # Second run
        _init_setup(self.test_dir)
        with open(hook_path, "r") as f:
            content2 = f.read()
            self.assertEqual(content2.count(".lisa/lisa.sh hooks story-in-dev"), 1)

if __name__ == "__main__":
    unittest.main()
