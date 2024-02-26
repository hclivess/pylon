import requests
import numpy as np
import time
from threading import Semaphore, Thread
import queue
import matplotlib.pyplot as plt

# Configuration
URL = "https://zjistil.cz/random"
NUM_REQUESTS = 100
TIMEOUT = 10
USERS_PER_MINUTE_LIMIT = 500
CONCURRENT_LIMIT = 40

# Initialize
results = {"success": 0, "failure": 0}
response_times = []
q = queue.Queue()  # Queue to manage the dispatching rate

# Semaphore for concurrency control
semaphore = Semaphore(CONCURRENT_LIMIT)

def fetch_url():
    while not q.empty():
        q.get()
        with semaphore:
            try:
                start_time = time.time()
                response = requests.get(URL, timeout=TIMEOUT)
                response_time = time.time() - start_time
                if response.status_code == 200:
                    results["success"] += 1
                    print(f"{results['success']+results['failure']}/{NUM_REQUESTS} ok - {response_time}")

                else:
                    results["failure"] += 1
                    print("bad")
                response_times.append(response_time)
            except requests.RequestException:
                results["failure"] += 1
                print("bad")
            finally:
                q.task_done()
                time.sleep(60 / USERS_PER_MINUTE_LIMIT)  # Control dispatch rate

# Populate the queue
for _ in range(NUM_REQUESTS):
    q.put(None)

# Start threads
threads = [Thread(target=fetch_url) for _ in range(CONCURRENT_LIMIT)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

# Results
avg_response_time = np.mean(response_times) if response_times else 0
print(f"Completed. Successes: {results['success']}, Failures: {results['failure']}, Average Response Time: {avg_response_time:.2f}s")

# Plotting the results
plt.figure(figsize=(12, 6))

# Plot 1: Success and Failure Counts
plt.subplot(1, 2, 1)
categories = ['Successes', 'Failures']
values = [results['success'], results['failure']]
plt.bar(categories, values, color=['green', 'red'])
plt.ylabel('Count')
plt.title('Load Test Results: Successes & Failures')

# Plot 2: Response Times Over Time (Line Plot)
plt.subplot(1, 2, 2)
# Generate a sequence of request numbers to use as the X-axis
request_numbers = list(range(1, len(response_times) + 1))
plt.plot(request_numbers, response_times, label='Response Time', linestyle='-', color='blue')
plt.axhline(y=avg_response_time, color='r', linestyle='-', label=f'Average: {avg_response_time:.2f}s')
plt.xlabel('Request Number')
plt.ylabel('Response Time (s)')
plt.title('Response Times of Requests')
plt.legend()

plt.tight_layout()
plt.show()