import sys
from .runner import run_test

def verify_fail(args):
    """
    Verifies that a test fails.
    Usage: lisa verify-fail <test_file> [--interactive]
    """
    if not args:
        print("Usage: lisa verify-fail <test_file> [--interactive]")
        return 1
        
    test_file = args[0]
    interactive = "--interactive" in args
    
    print(f"\n[LISA] TDD Gate: Verifying RED State for {test_file}")
    print("---------------------------------------------------")
    
    # 1. Verification (Interactive Optional)
    if interactive:
        print(f"File: {test_file}")
        try:
            response = input("Does this test accurately reflect the requirement and is expected to fail? [y/N] ").strip().lower()
        except KeyboardInterrupt:
            print("\n[LISA] Aborted by user.")
            return 1

        if response != 'y':
            print("[LISA] Verification rejected. Please revise the test.")
            return 1
    else:
        print("[LISA] Automated Mode (Non-interactive)")
        
    # 2. Automated Fail Verification
    print(f"\n[LISA] Running test (Expecting Failure)...")
    ret_code = run_test(test_file)
    
    if ret_code == 0:
        print(f"\n[LISA] [ERROR] Test Passed! Expected failure (RED state).")
        print("Please check that the test is actually asserting the new behavior.")
        return 1
    else:
        print(f"\n[LISA] [SUCCESS] RED State Verified. Test failed as expected.")
        return 0

def verify_pass(args):
    """
    Verifies that a test passes.
    Usage: lisa verify-pass <test_file>
    """
    if not args:
        print("Usage: lisa verify-pass <test_file>")
        return 1

    test_file = args[0]
    
    print(f"\n[LISA] TDD Gate: Verifying GREEN State for {test_file}")
    print("---------------------------------------------------")
    
    # 1. Automated Pass Verification
    print("\n[LISA] Running test (Expecting Success)...")
    ret_code = run_test(test_file)
    
    if ret_code != 0:
        print(f"\n[LISA] [ERROR] Test Failed! Expected success (GREEN state).")
        print("Please fix the implementation or test.")
        return 1
    else:
        print(f"\n[LISA] [SUCCESS] Test Passed. Cycle Complete.")
        return 0
