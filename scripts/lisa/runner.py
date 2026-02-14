import subprocess
import os

def run_test(test_file):
    """
    Runs a specific test file using accessible runners.
    Tries pytest first, falls back to unittest.
    Returns return code (0 = passed, != 0 failed).
    """
    if not os.path.exists(test_file):
        raise FileNotFoundError(f"Test file not found: {test_file}")

    # Try pytest
    # We use subprocess run to capture output but usually we want to show it to user
    # For interactive verification, showing output is good.
    try:
        # Check if pytest is installed/available
        subprocess.run(["pytest", "--version"], check=True, capture_output=True)
        return subprocess.call(["pytest", test_file])
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to python unittest
        try:
            return subprocess.call(["python3", "-m", "unittest", test_file])
        except subprocess.CalledProcessError:
             return 1
