"""
API Request Tracker for monitoring LLM API usage.
Tracks requests per session and provides statistics.
"""
from typing import Dict, Optional
from datetime import datetime
from threading import Lock


class APITracker:
    """Thread-safe API request tracker."""
    
    def __init__(self):
        self._counts: Dict[str, int] = {}
        self._lock = Lock()
        self._session_start = datetime.now()
    
    def increment(self, provider: str = "default"):
        """Increment request count for a provider."""
        with self._lock:
            if provider not in self._counts:
                self._counts[provider] = 0
            self._counts[provider] += 1
    
    def get_count(self, provider: Optional[str] = None) -> int:
        """Get request count for a provider or total."""
        with self._lock:
            if provider:
                return self._counts.get(provider, 0)
            return sum(self._counts.values())
    
    def get_all_counts(self) -> Dict[str, int]:
        """Get all provider counts."""
        with self._lock:
            return self._counts.copy()
    
    def reset(self):
        """Reset all counters."""
        with self._lock:
            self._counts.clear()
            self._session_start = datetime.now()
    
    def get_session_duration(self) -> float:
        """Get session duration in seconds."""
        return (datetime.now() - self._session_start).total_seconds()
    
    def get_summary(self) -> str:
        """Get formatted summary of API usage."""
        total = self.get_count()
        duration = self.get_session_duration()
        
        summary = [
            f"\n{'='*50}",
            f"API Request Summary",
            f"{'='*50}",
            f"Total Requests: {total}",
            f"Session Duration: {duration:.1f}s",
        ]
        
        if len(self._counts) > 1:
            summary.append("\nBy Provider:")
            for provider, count in sorted(self._counts.items()):
                summary.append(f"  {provider}: {count}")
        
        summary.append(f"{'='*50}\n")
        return "\n".join(summary)


# Global tracker instance
_global_tracker = APITracker()


def get_tracker() -> APITracker:
    """Get the global API tracker instance."""
    return _global_tracker


def track_request(provider: str = "default"):
    """Decorator to track API requests."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            _global_tracker.increment(provider)
            return func(*args, **kwargs)
        return wrapper
    return decorator
