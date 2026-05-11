import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

import tiktoken
from app.config import get_settings

logger = logging.getLogger(__name__)

class UsageTracker:
    """
    Tracks AI usage and estimates costs in USD.
    Uses tiktoken for accurate token counting.
    """

    def __init__(self):
        self.settings = get_settings()
        self.records: List[Dict[str, Any]] = []
        
        # Simple pricing table (Price per 1M tokens in USD)
        # Format: (input_price, output_price)
        self.pricing_table = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (5.00, 15.00),
            "gpt-4-turbo-preview": (10.00, 30.00),
            "claude-3-opus-20240229": (15.00, 75.00),
            "claude-3-sonnet-20240229": (3.00, 15.00),
            "gemini-1.5-pro": (3.50, 10.50),
            "gemini-2.0-flash": (0.10, 0.40),
            "gemini-3-flash-preview": (0.10, 0.40),
            "gemini-flash-latest": (0.10, 0.40),
        }
        
        logger.info("Usage Tracker initialized.")

    def _count_tokens(self, text: str, model: str | None = None) -> int:
        """
        Count the number of tokens in a string using tiktoken.
        Falls back to a rough estimation if the model is not supported.
        """
        if not text:
            return 0
            
        try:
            # Use gpt-4 encoding 
            encoding_model = model if model and "gpt" in model else "gpt-4"
            encoding = tiktoken.encoding_for_model(encoding_model)
            return len(encoding.encode(text))
        except Exception:
            # Rough fallback: ~4 characters per token
            return len(text) // 4

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate the cost of a request based on the pricing table."""
        prices = self.pricing_table.get(model, (0.0, 0.0))
        input_cost = (prompt_tokens / 1_000_000) * prices[0]
        output_cost = (completion_tokens / 1_000_000) * prices[1]
        return input_cost + output_cost

    def record_usage(self, provider: str, model: str, prompt: str, completion: str) -> Dict[str, Any]:
        """
        Record a single AI request/response pair and calculate usage metrics.
        """
        prompt_tokens = self._count_tokens(prompt, model)
        completion_tokens = self._count_tokens(completion, model)
        total_tokens = prompt_tokens + completion_tokens
        
        estimated_cost = self._estimate_cost(model, prompt_tokens, completion_tokens)
        
        record = {
            "timestamp": datetime.now(),
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost
        }
        
        self.records.append(record)
        logger.info(f"Recorded usage for {model} ({provider}): {total_tokens} tokens, ${estimated_cost:.6f}")
        return record

    def get_daily_cost(self) -> float:
        """Calculate the total estimated cost for the current day."""
        today = datetime.now().date()
        daily_records = [
            r for r in self.records 
            if r["timestamp"].date() == today
        ]
        return sum(r["estimated_cost"] for r in daily_records)

    def get_total_requests(self) -> int:
        """Return the total number of requests recorded."""
        return len(self.records)
