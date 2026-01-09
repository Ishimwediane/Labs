"""Output formatting and file I/O for scraping results."""

import json
from pathlib import Path
from typing import List
from .models import PageMetadata


def save_results_to_json(results: List[PageMetadata], filename: str) -> None:
    """
    Save scraping results to a JSON file.
    
    Args:
        results: List of PageMetadata objects
        filename: Output filename
    """
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / filename
    
    # Convert PageMetadata objects to dictionaries
    data = [
        {
            "url": r.url,
            "title": r.title,
            "description": r.description,
            "status_code": r.status_code,
            "fetch_time": round(r.fetch_time, 3),
            "error": r.error
        }
        for r in results
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Results saved to {output_path}")


def print_summary(results: List[PageMetadata], method: str, elapsed: float) -> None:
    """
    Print a summary of scraping results.
    
    Args:
        results: List of PageMetadata objects
        method: Scraping method name
        elapsed: Total elapsed time
    """
    successful = sum(1 for r in results if r.status_code == 200)
    failed = len(results) - successful
    
    print(f"\n{'='*60}")
    print(f"{method.upper()} SCRAPING RESULTS")
    print(f"{'='*60}")
    print(f"Total URLs: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total Time: {elapsed:.2f}s")
    print(f"Average Time per URL: {elapsed/len(results):.2f}s")
    print(f"{'='*60}\n")
