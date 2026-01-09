import asyncio
import time
from typing import List
from .models import PageMetadata
from .scraper import scrape_sequential, scrape_threaded, scrape_async
from .output import print_summary


def run_sequential_scraper(urls: List[str]) -> tuple[List[PageMetadata], float]:
    """Run sequential scraper and return results with timing."""
    print("\n[*] Running Sequential Scraper...")
    start = time.perf_counter()
    results = scrape_sequential(urls)
    elapsed = time.perf_counter() - start
    print_summary(results, "Sequential", elapsed)
    return results, elapsed


def run_threaded_scraper(urls: List[str]) -> tuple[List[PageMetadata], float]:
    """Run threaded scraper and return results with timing."""
    print("\n[*] Running Threaded Scraper...")
    start = time.perf_counter()
    results = scrape_threaded(urls, max_workers=10)
    elapsed = time.perf_counter() - start
    print_summary(results, "Threaded", elapsed)
    return results, elapsed


def run_async_scraper(urls: List[str]) -> tuple[List[PageMetadata], float]:
    """Run async scraper and return results with timing."""
    print("\n[*] Running Async Scraper...")
    start = time.perf_counter()
    results = asyncio.run(scrape_async(urls, max_concurrent=10))
    elapsed = time.perf_counter() - start
    print_summary(results, "Async", elapsed)
    return results, elapsed


def print_performance_comparison(
    seq_time: float,
    thread_time: float,
    async_time: float
) -> None:
    """
    Print performance comparison between all three methods.
    
    Args:
        seq_time: Sequential scraping time
        thread_time: Threaded scraping time
        async_time: Async scraping time
    """
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    print(f"Sequential: {seq_time:.2f}s (baseline)")
    print(f"Threaded:   {thread_time:.2f}s ({seq_time/thread_time:.2f}x faster)")
    print(f"Async:      {async_time:.2f}s ({seq_time/async_time:.2f}x faster)")
    print("="*60)
    
    # Determine winner
    fastest = min(seq_time, thread_time, async_time)
    if fastest == async_time:
        winner = "Async"
    elif fastest == thread_time:
        winner = "Threaded"
    else:
        winner = "Sequential"
    
    print(f"\n🏆 Winner: {winner} approach")
    print()
