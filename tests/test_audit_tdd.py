import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from scripts.lisa.commands import verify_fail, verify_pass

class TestAuditTDD(unittest.TestCase):
    
    @patch('scripts.lisa.commands.run_test')
    def test_verify_fail_default_success(self, mock_run_test):
        # Scenario: Default mode (no input), test fails (rc=1) -> Success (0)
        mock_run_test.return_value = 1
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # No input should be requested
        result = verify_fail(["tests/dummy.py"])
        
        sys.stdout = sys.__stdout__
        
        self.assertEqual(result, 0)
        self.assertIn("RED State Verified", captured_output.getvalue())
        mock_run_test.assert_called_once()

    @patch('scripts.lisa.commands.run_test')
    def test_verify_fail_default_error_passes(self, mock_run_test):
        # Scenario: Default mode, test passes (rc=0) -> Error (1)
        mock_run_test.return_value = 0
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        result = verify_fail(["tests/dummy.py"])
        
        sys.stdout = sys.__stdout__
        
        self.assertEqual(result, 1)
        self.assertIn("Test Passed! Expected failure", captured_output.getvalue())

    @patch('scripts.lisa.commands.run_test')
    @patch('builtins.input', return_value='y')
    def test_verify_fail_interactive_success(self, mock_input, mock_run_test):
        # Scenario: Interactive mode (--interactive), User 'y', Test Fails -> Success
        mock_run_test.return_value = 1
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        result = verify_fail(["tests/dummy.py", "--interactive"])
        
        sys.stdout = sys.__stdout__
        
        self.assertEqual(result, 0)
        # Verify input was called with prompt
        mock_input.assert_called_once()
        self.assertIn("Does this test accurately reflect", mock_input.call_args[0][0])
        mock_run_test.assert_called_once()

    @patch('scripts.lisa.commands.run_test')
    def test_verify_pass_success(self, mock_run_test):
        # Scenario: Test passes (rc=0) -> Success
        mock_run_test.return_value = 0
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        result = verify_pass(["tests/dummy.py"])
        
        sys.stdout = sys.__stdout__
        
        self.assertEqual(result, 0)
        self.assertIn("Test Passed. Cycle Complete", captured_output.getvalue())

if __name__ == '__main__':
    unittest.main()
