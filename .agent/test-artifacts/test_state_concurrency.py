import multiprocessing
import os
import time
import sys
# Add scripts to path so we can import lisa
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts")))

from lisa.state import StateManager

def worker(worker_id, iterations):
    """Worker function to update state concurrently."""
    manager = StateManager(state_file=".lisa-test/state.json")
    
    for i in range(iterations):
        # We simulate work by updating a unique key for each worker.
        # This implementation tests that:
        # 1. Multiple processes can write to the same file without corruption (valid JSON).
        # 2. Key-level updates are preserved (last-write-wins per key), demonstrating no data loss from race conditions on the file content.
        manager.update(f"worker_{worker_id}", i)

if __name__ == "__main__":
    # Clean up
    if os.path.exists(".lisa-test"):
        import shutil
        shutil.rmtree(".lisa-test")
    
    manager = StateManager(state_file=".lisa-test/state.json")
    
    workers = []
    num_workers = 5
    iterations = 50
    
    print(f"Starting {num_workers} workers with {iterations} iterations each...")
    start_time = time.time()
    
    for i in range(num_workers):
        p = multiprocessing.Process(target=worker, args=(i, iterations))
        workers.append(p)
        p.start()
        
    for p in workers:
        p.join()
        
    end_time = time.time()
    print(f"Finished in {end_time - start_time:.2f} seconds.")
    
    # Verify state
    final_state = manager.load()
    print("Final State Keys:", final_state.keys())
    
    expected_keys = {f"worker_{i}" for i in range(num_workers)} | {"taskId", "status", "mode", "lastUpdated"}
    found_keys = set(final_state.keys())
    
    if expected_keys.issubset(found_keys):
        print("SUCCESS: All worker updates persisted.")
        
        # Verify values
        for i in range(num_workers):
            if final_state[f"worker_{i}"] != iterations - 1:
                print(f"FAILURE: Worker {i} did not reach expected count. Got {final_state[f'worker_{i}']}")
                sys.exit(1)
        print("SUCCESS: All worker values correct.")
    else:
        print(f"FAILURE: Missing keys. Expected {expected_keys}, Found {found_keys}")
        sys.exit(1)
