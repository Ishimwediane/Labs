# Lab 5: Async Web Scraper with asyncio Fundamentals

A high-performance web scraper that demonstrates the power of asynchronous programming in Python. This project implements three different approaches to web scraping (Sequential, Threaded, and Async) and compares their performance.

## Features

- **Three Scraping Approaches**:
  - Sequential: Traditional synchronous scraping
  - Threaded: Concurrent scraping using ThreadPoolExecutor
  - Async: High-performance async scraping with asyncio and aiohttp

- **Advanced asyncio Concepts**:
  - Event loop management
  - Coroutines with `async`/`await`
  - Concurrent task execution with `asyncio.gather()` and `asyncio.create_task()`
  - Timeout handling with `asyncio.wait_for()`
  - Semaphores for rate limiting

- **Decorators**:
  - `@retry`: Automatic retry logic for failed requests
  - `@log_execution`: Execution time logging

- **Async Generators**:
  - Async response processing
  - Batch processing with `async for`

- **Metadata Extraction**:
  - Page titles using BeautifulSoup
  - Meta descriptions with regex and BeautifulSoup
  - Open Graph metadata support

## Setup

1. **Python Version**: Requires Python 3.11+

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Additional Dependency** (for sequential scraper):
   ```bash
   pip install requests
   ```

## Usage

Run the main script to execute all three scrapers and compare performance:

```bash
python -m src.main
```

This will:
1. Scrape 20 URLs using all three methods
2. Display performance metrics for each approach
3. Save results to JSON files in the `data/` directory
4. Show a performance comparison summary

## Project Structure

```
Lab 5 Solution/
├── src/
│   ├── __init__.py
│   ├── main.py          # Entry point and benchmarking
│   ├── scraper.py       # Core scraping implementations
│   ├── utils.py         # Decorators and async generators
│   └── urls.py          # Sample URLs for testing
├── tests/
│   ├── __init__.py
│   ├── test_utils.py    # Tests for utilities
│   └── test_scraper.py  # Tests for scrapers
├── data/                # Output directory for results
├── docs/                # Additional documentation
├── requirements.txt
└── README.md
```

## Understanding asyncio

### What is asyncio?

`asyncio` is Python's built-in library for writing concurrent code using the `async`/`await` syntax. It's particularly effective for I/O-bound operations like web scraping, where the program spends most of its time waiting for network responses.

### Key Concepts

1. **Coroutines**: Functions defined with `async def` that can be paused and resumed
2. **Event Loop**: Manages and executes async tasks
3. **await**: Pauses coroutine execution until the awaited operation completes
4. **Tasks**: Wrapped coroutines that run concurrently

### Why Async for Web Scraping?

- **Non-blocking I/O**: While waiting for one request, the program can initiate others
- **Efficient Resource Usage**: Single-threaded but handles multiple requests
- **Better Performance**: Significantly faster than sequential for I/O-bound tasks

## Performance Comparison

Based on typical results with 20 URLs:

| Method     | Time    | Speedup |
|------------|---------|---------|
| Sequential | ~45s    | 1x      |
| Threaded   | ~8s     | 5-6x    |
| Async      | ~4s     | 10-12x  |

**Key Findings**:
- **Async is fastest**: Minimal overhead, efficient I/O handling
- **Threading is good**: Better than sequential, but has thread management overhead
- **Sequential is slowest**: Waits for each request to complete before starting the next

### Why Async Wins

1. **Lower Overhead**: No thread creation/management costs
2. **Cooperative Multitasking**: Explicit control flow with `await`
3. **Scalability**: Can handle thousands of concurrent connections
4. **Memory Efficient**: Single-threaded, lower memory footprint

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Sample Output

```
============================================================
ASYNC WEB SCRAPER - Performance Comparison
============================================================

Scraping 20 URLs using 3 different approaches:

1. Sequential (one at a time)
2. Threaded (concurrent threads)
3. Async (asyncio + aiohttp)

🔄 Running Sequential Scraper...

============================================================
SEQUENTIAL SCRAPING RESULTS
============================================================
Total URLs: 20
Successful: 18
Failed: 2
Total Time: 45.32s
Average Time per URL: 2.27s
============================================================

🔄 Running Threaded Scraper...

============================================================
THREADED SCRAPING RESULTS
============================================================
Total URLs: 20
Successful: 18
Failed: 2
Total Time: 8.15s
Average Time per URL: 0.41s
============================================================

🔄 Running Async Scraper...

============================================================
ASYNC SCRAPING RESULTS
============================================================
Total URLs: 20
Successful: 18
Failed: 2
Total Time: 3.92s
Average Time per URL: 0.20s
============================================================

✓ Results saved to data/sequential_results.json
✓ Results saved to data/threaded_results.json
✓ Results saved to data/async_results.json

============================================================
PERFORMANCE COMPARISON
============================================================
Sequential: 45.32s (baseline)
Threaded:   8.15s (5.56x faster)
Async:      3.92s (11.56x faster)
============================================================

🏆 Winner: Async approach
```

## Key Learnings

1. **Async is ideal for I/O-bound tasks** like web scraping, API calls, and database queries
2. **Threading has overhead** but is still much better than sequential
3. **Decorators enhance async functions** with retry logic and logging
4. **Semaphores control concurrency** to avoid overwhelming servers
5. **Error handling is crucial** in async code to prevent task failures from cascading

## License

This project is for educational purposes as part of the Python Advanced course.
