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

    import sys
    # Try pytest
    # We use subprocess run to capture output but usually we want to show it to user
    # For interactive verification, showing output is good.
    try:
        # Check if pytest is installed/available
        subprocess.run([sys.executable, "-m", "pytest", "--version"], check=True, capture_output=True)
        return subprocess.call([sys.executable, "-m", "pytest", test_file])
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to python unittest
        try:
            return subprocess.call([sys.executable, "-m", "unittest", test_file])
        except subprocess.CalledProcessError:
             return 1
