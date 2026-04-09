import time
import timeit
from unittest.mock import MagicMock

# Simulate a database overhead per call (I/O, network, processing)
DB_OVERHEAD = 0.001 # 1ms

def simulate_n_plus_one(n, existing_urls):
    db_calls = 0
    results = []
    total_db_time = 0
    for i in range(n):
        url = f"https://example.com/thing/{i}"
        db_calls += 1
        total_db_time += DB_OVERHEAD
        if url in existing_urls:
            results.append("existing")
        else:
            results.append("new")
    time.sleep(total_db_time)
    return results, db_calls

def simulate_batch(n, existing_urls):
    db_calls = 0
    results = []
    urls_to_check = [f"https://example.com/thing/{i}" for i in range(n)]
    db_calls += 1
    time.sleep(DB_OVERHEAD) # Only one overhead
    existing_in_db = {url for url in urls_to_check if url in existing_urls}
    for url in urls_to_check:
        if url in existing_in_db:
            results.append("existing")
        else:
            results.append("new")
    return results, db_calls

if __name__ == "__main__":
    for n in [10, 100]:
        existing_urls = {f"https://example.com/thing/{i}" for i in range(0, n, 2)}

        # Use a smaller number of iterations since we are sleeping
        n_plus_one_time = timeit.timeit(lambda: simulate_n_plus_one(n, existing_urls), number=10)
        batch_time = timeit.timeit(lambda: simulate_batch(n, existing_urls), number=10)

        print(f"Items processed: {n}")
        print(f"  N+1 Approach - Time: {n_plus_one_time:.4f}s, DB Calls: {n}")
        print(f"  Batch Approach - Time: {batch_time:.4f}s, DB Calls: 1")
        print(f"  Improvement: {(n_plus_one_time - batch_time) / n_plus_one_time * 100:.2f}%")
