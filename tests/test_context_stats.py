
import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# We expect this module to verify, even if it doesn't exist yet (TDD)
from scripts.lisa.context_stats import count_tokens, get_context_health, scan_workspace

class TestContextStats(unittest.TestCase):
    
    def test_count_tokens_heuristic(self):
        """Test that count_tokens uses the char/4 heuristic."""
        # 4 chars = 1 token
        self.assertEqual(count_tokens("1234"), 1)
        # 8 chars = 2 tokens
        self.assertEqual(count_tokens("12345678"), 2)
        # Empty = 0
        self.assertEqual(count_tokens(""), 0)
        # Rounding? "12345" (5 chars) -> 1.25 -> usually ceil or floor?
        # Plan didn't specify, but standard estimation usually rounds up or keeps decimals.
        # Let's assume math.ceil or check implementation. 
        # For 'stats' usually integer tokens are preferred. 
        # Let's assume standard len(text)/4.0 for now, or just integer division if simple.
        # Let's Assert approximate or >= 1 for 5 chars if we want safety, 
        # but technically 5/4 = 1.25. 
        # Let's stick to simple multiples of 4 for the strict test for now.
        self.assertEqual(count_tokens("abcd" * 100), 100)

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

    def test_scan_workspace_integration(self):
        """Integration test with a temp directory."""
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
            
            total_tokens = scan_workspace(test_dir, ignores=[".git"])
            self.assertEqual(total_tokens, 3)
            
        finally:
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    unittest.main()
