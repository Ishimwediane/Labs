import logging
import json
from app.infrastructure.cache import CacheService
from app.infrastructure.rate_limiter import TokenBucketRateLimiter, RateLimitExceededError
from app.infrastructure.usage_tracker import UsageTracker
from app.config import get_settings

# Configure minimal logging for the test output
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def run_cache_test():
    print("\n--- [Scenario 1: CacheService Validation] ---")
    cache = CacheService()
    
    payload = {"query": "Tell me about libraries", "model": "gemini-3-flash"}
    
    # 1. Test deterministic key generation
    key1 = cache.make_key("rag_search", payload)
    key2 = cache.make_key("rag_search", payload)
    
    print(f"Key 1: {key1}")
    print(f"Key 2: {key2}")
    
    if key1 == key2:
        print("[SUCCESS] Success: Keys are deterministic and match.")
    else:
        print("[ERROR] Error: Keys do not match.")

    # 2. Test store and retrieve
    sample_data = {"result": "Libraries are amazing places for learning.", "tokens": 12}
    
    set_success = cache.set(key1, sample_data, ttl=60)
    
    if cache.enabled:
        if set_success:
            retrieved = cache.get(key1)
            if retrieved == sample_data:
                print("[SUCCESS] Success: Cached data retrieved correctly.")
            else:
                print(f"[ERROR] Error: Retrieved data mismatch. Got: {retrieved}")
        else:
            print("[ERROR] Error: Failed to set cache even though it's enabled.")
    else:
        print("[INFO] Note: Cache is disabled (Redis unavailable), but app correctly continues.")

def run_rate_limiter_test():
    print("\n--- [Scenario 2: Rate Limiter Validation] ---")
    limiter = TokenBucketRateLimiter()
    settings = get_settings()
    limit = settings.RATE_LIMIT_PER_MINUTE
    
    print(f"Testing rate limit: {limit} requests per minute.")
    
    try:
        # We try to acquire one more than the limit to trigger the exception
        for i in range(limit + 1):
            limiter.acquire()
            if (i + 1) % 10 == 0 or i == 0:
                print(f"Acquired token {i+1}...")
        
        print("[ERROR] Error: Limit was not hit as expected.")
    except RateLimitExceededError as e:
        print(f"[SUCCESS] Success: Rate limit hit as expected at request {limit + 1}.")
        print(f"Exception message: {e}")

def run_usage_tracker_test():
    print("\n--- [Scenario 3: UsageTracker Validation] ---")
    tracker = UsageTracker()
    
    provider = "google"
    model = "gemini-3-flash-preview"
    prompt = "What is the capital of Rwanda?"
    completion = "The capital of Rwanda is Kigali."
    
    # 1. Record usage
    record = tracker.record_usage(provider, model, prompt, completion)
    print("Record created:")
    print(json.dumps({k: str(v) for k, v in record.items()}, indent=2))
    
    # 2. Check metrics
    total_reqs = tracker.get_total_requests()
    daily_cost = tracker.get_daily_cost()
    
    print(f"Total Request Count: {total_reqs}")
    print(f"Total Daily Cost: ${daily_cost:.6f}")
    
    if total_reqs == 1 and daily_cost > 0:
        print("[SUCCESS] Success: Usage tracked and cost is non-zero.")
    else:
        print(f"[ERROR] Error: Metrics check failed. Reqs: {total_reqs}, Cost: {daily_cost}")

if __name__ == "__main__":
    print("=== LibraryMind Part 2: Infrastructure Manual Validation ===")
    
    run_cache_test()
    run_rate_limiter_test()
    run_usage_tracker_test()
    
    print("\n=== Validation Complete ===")
