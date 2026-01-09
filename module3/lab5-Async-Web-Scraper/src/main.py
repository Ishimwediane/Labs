"""Main entry point for the Async Web Scraper."""

from .benchmark import (
    run_sequential_scraper,
    run_threaded_scraper,
    run_async_scraper,
    print_performance_comparison
)
from .output import save_results_to_json
from .urls import SAMPLE_URLS


def main():
    """Main function to run all scrapers and compare performance."""
    print("\n" + "="*60)
    print("ASYNC WEB SCRAPER - Performance Comparison")
    print("="*60)
    
    # Use a subset of URLs for faster testing (or all for full benchmark)
    urls = SAMPLE_URLS[:20]  # Using first 20 URLs
    
    print(f"\nScraping {len(urls)} URLs using 3 different approaches:\n")
    print("1. Sequential (one at a time)")
    print("2. Threaded (concurrent threads)")
    print("3. Async (asyncio + aiohttp)")
    
    # Run all three scrapers
    seq_results, seq_time = run_sequential_scraper(urls)
    thread_results, thread_time = run_threaded_scraper(urls)
    async_results, async_time = run_async_scraper(urls)
    
    # Save results
    save_results_to_json(seq_results, "sequential_results.json")
    save_results_to_json(thread_results, "threaded_results.json")
    save_results_to_json(async_results, "async_results.json")
    
    # Print comparison
    print_performance_comparison(seq_time, thread_time, async_time)


if __name__ == "__main__":
    main()
