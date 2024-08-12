import asyncio
import aiohttp
import numpy as np
import time
from collections import deque
import matplotlib.pyplot as plt

# Configuration
URL = "https://zjistil.cz/random"
NUM_REQUESTS = 100
TIMEOUT = 10
USERS_PER_MINUTE_LIMIT = 500
CONCURRENT_LIMIT = 40

class LoadTester:
    def __init__(self):
        self.results = {"success": 0, "failure": 0}
        self.response_times = deque(maxlen=NUM_REQUESTS)
        self.semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
        self.rate_limiter = asyncio.Semaphore(USERS_PER_MINUTE_LIMIT)

    async def fetch_url(self, session, request_number):
        async with self.semaphore:
            try:
                start_time = time.time()
                async with session.get(URL, timeout=TIMEOUT) as response:
                    await response.text()
                response_time = time.time() - start_time
                if response.status == 200:
                    self.results["success"] += 1
                    print(f"{request_number}/{NUM_REQUESTS} ok - {response_time:.2f}s")
                else:
                    self.results["failure"] += 1
                    print(f"{request_number}/{NUM_REQUESTS} bad - Status: {response.status}")
                self.response_times.append(response_time)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.results["failure"] += 1
                print(f"{request_number}/{NUM_REQUESTS} bad - Error: {str(e)}")
            finally:
                self.rate_limiter.release()

    async def run_test(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(1, NUM_REQUESTS + 1):
                await self.rate_limiter.acquire()
                task = asyncio.create_task(self.fetch_url(session, i))
                tasks.append(task)
            await asyncio.gather(*tasks)

    def plot_results(self):
        plt.figure(figsize=(12, 6))

        # Plot 1: Success and Failure Counts
        plt.subplot(1, 2, 1)
        categories = ['Successes', 'Failures']
        values = [self.results['success'], self.results['failure']]
        plt.bar(categories, values, color=['green', 'red'])
        plt.ylabel('Count')
        plt.title('Load Test Results: Successes & Failures')

        # Plot 2: Response Times Over Time (Line Plot)
        plt.subplot(1, 2, 2)
        request_numbers = list(range(1, len(self.response_times) + 1))
        plt.plot(request_numbers, self.response_times, label='Response Time', linestyle='-', color='blue')
        avg_response_time = np.mean(self.response_times)
        plt.axhline(y=avg_response_time, color='r', linestyle='-', label=f'Average: {avg_response_time:.2f}s')
        plt.xlabel('Request Number')
        plt.ylabel('Response Time (s)')
        plt.title('Response Times of Requests')
        plt.legend()

        plt.tight_layout()
        plt.show()

    def print_results(self):
        avg_response_time = np.mean(self.response_times) if self.response_times else 0
        print(f"Completed. Successes: {self.results['success']}, Failures: {self.results['failure']}, "
              f"Average Response Time: {avg_response_time:.2f}s")

async def main():
    tester = LoadTester()
    await tester.run_test()
    tester.print_results()
    tester.plot_results()

if __name__ == "__main__":
    asyncio.run(main())
