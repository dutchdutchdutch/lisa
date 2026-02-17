
import math
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# We expect this module to verify, even if it doesn't exist yet (TDD)
from scripts.lisa.context_stats import count_tokens, get_context_health, scan_workspace, MAX_FILE_SIZE

class TestContextStats(unittest.TestCase):
    # ...

    def test_scan_workspace_large_file(self):
        """Test that files larger than MAX_FILE_SIZE use heuristic and are not read."""
        test_dir = tempfile.mkdtemp()
        try:
            # Create a dummy file so os.walk finds it
            file_path = os.path.join(test_dir, "large_file.txt")
            with open(file_path, "w") as f:
                f.write("content") # content doesn't matter, mocked size does

            large_size = MAX_FILE_SIZE + 400
            expected_tokens = math.ceil(large_size / 4)

            # Patch getsize to simulate large file
            with patch('scripts.lisa.context_stats.os.path.getsize', return_value=large_size):
                # Patch open to verify it is NOT called for reading
                # Note: 'builtins.open' patches everywhere, so we must be careful.
                # scan_workspace uses `open(..., 'r', ...)`
                # We mock it to ensure it's not called.
                with patch('builtins.open', new_callable=MagicMock) as mock_open:
                     # os.walk might call strict open? No.
                     # But we need to ensure the walk still works? 
                     # os.walk uses os.scandir which doesn't open files.
                     
                     total, count = scan_workspace(test_dir)
                     
                     self.assertEqual(total, expected_tokens)
                     self.assertEqual(count, 1)
                     
                     # Verify open was NOT called
                     mock_open.assert_not_called()
        finally:
            shutil.rmtree(test_dir)


    
    @patch('scripts.lisa.context_stats.ENCODING', None) # Force Heuristic
    def test_count_tokens_heuristic(self):
        """Test that count_tokens uses the char/4 heuristic when tiktoken missing."""
        # 4 chars = 1 token
        self.assertEqual(count_tokens("1234"), 1)
        # 8 chars = 2 tokens
        self.assertEqual(count_tokens("12345678"), 2)
        # Empty = 0
        self.assertEqual(count_tokens(""), 0)
        # 100 chars -> 25 tokens
        self.assertEqual(count_tokens("abcd" * 25), 25)

    def test_count_tokens_tiktoken(self):
        """Test that count_tokens uses tiktoken if available."""
        # Mock encoding object
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3] # simulate 3 tokens
        
        with patch('scripts.lisa.context_stats.ENCODING', mock_encoding):
            count = count_tokens("some text")
            self.assertEqual(count, 3)
            # Ensure special tokens are disallowed as per implementation
            mock_encoding.encode.assert_called_with("some text", disallowed_special=())

    def test_get_context_health(self):
        """Test health status thresholds."""
        limit = 1000
        
        # < 70% (0-699) -> GREEN
        self.assertEqual(get_context_health(0, limit), "GREEN")
        self.assertEqual(get_context_health(699, limit), "GREEN")
        
        # 70-90% (700-900) -> AMBER
        self.assertEqual(get_context_health(700, limit), "AMBER")
        self.assertEqual(get_context_health(900, limit), "AMBER")
        
        # > 90% (901+) -> RED
        self.assertEqual(get_context_health(901, limit), "RED")
        self.assertEqual(get_context_health(1000, limit), "RED")
        self.assertEqual(get_context_health(1500, limit), "RED")

    @patch('scripts.lisa.context_stats.ENCODING', None) # Force Heuristic
    def test_scan_workspace_integration(self):
        """Integration test with a temp directory (using heuristic fallback)."""
        # Create a temp dir
        test_dir = tempfile.mkdtemp()
        try:
            # Create File A: "1234" (1 token)
            with open(os.path.join(test_dir, "file_a.txt"), "w") as f:
                f.write("1234")
            
            # Create File B: "12345678" (2 tokens)
            # Create in subdir
            sub_dir = os.path.join(test_dir, "subdir")
            os.mkdir(sub_dir)
            with open(os.path.join(sub_dir, "file_b.txt"), "w") as f:
                f.write("12345678")
                
            # Create Ignored File (e.g. inside .git)
            git_dir = os.path.join(test_dir, ".git")
            os.mkdir(git_dir)
            with open(os.path.join(git_dir, "ignored.txt"), "w") as f:
                f.write("1234" * 1000) # Should be ignored
                
            # Total expected: 1 + 2 = 3 tokens.
            # Total files: 2 (ignored.txt is excluded)
            
            total_tokens, file_count = scan_workspace(test_dir, ignores=[".git"])
            self.assertEqual(total_tokens, 3)
            self.assertEqual(file_count, 2)
            
        finally:
            shutil.rmtree(test_dir)

    def test_scan_workspace_tiktoken(self):
        """Integration test with tiktoken mocked."""
        test_dir = tempfile.mkdtemp()
        try: 
            # Mock encoding
            mock_encoding = MagicMock()
            # 2 files, so called twice?
            # mock_encoding.encode.side_effect = [[1], [1, 2]] # 1 then 2 tokens
            # BUT scan_workspace iterates files in OS order, might vary.
            # Let's just return a constant for simplicity or depend on content.
            # Since we mock ENCODING.encode, we can inspect calls.
           
            mock_encoding.encode.return_value = [1]*10 # 10 tokens per file
            
            with open(os.path.join(test_dir, "file.txt"), "w") as f:
                f.write("content") # 10 tokens via mock

            with patch('scripts.lisa.context_stats.ENCODING', mock_encoding):
                total, count = scan_workspace(test_dir)
                self.assertEqual(total, 10)
                self.assertEqual(count, 1)

        finally:
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    unittest.main()
