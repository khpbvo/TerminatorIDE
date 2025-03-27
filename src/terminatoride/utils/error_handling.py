import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class APIError:
    message: str
    error_type: str
    status_code: Optional[int] = None
    is_retriable: bool = False


class RateLimitHandler:
    def __init__(self, max_requests: int = 50, time_window: int = 60):
        """Initialize rate limit handler

        Args:
            max_requests: Maximum number of requests allowed per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_timestamps: List[float] = []
        self.request_count = 0  # Added to match the test expectation

    def can_make_request(self) -> bool:
        """Check if a request can be made under current rate limits

        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()

        # Remove timestamps older than the time window
        self.request_timestamps = [
            ts for ts in self.request_timestamps if current_time - ts < self.time_window
        ]

        # Check if we're under the limit
        if len(self.request_timestamps) < self.max_requests:
            self.request_timestamps.append(current_time)
            self.request_count += 1  # Increment the request counter
            return True
        return False

    def time_until_next_request(self) -> float:
        """Calculate time until next request is allowed

        Returns:
            Time in seconds until next request is allowed
        """
        if self.can_make_request():
            return 0.0

        current_time = time.time()
        oldest_timestamp = min(self.request_timestamps)
        return max(0.0, self.time_window - (current_time - oldest_timestamp))


def handle_api_error(error_response: Dict[str, Any]) -> APIError:
    """Handle API error responses from OpenAI

    Args:
        error_response: Error response dictionary from the API

    Returns:
        APIError object with details
    """
    error = error_response.get("error", {})
    message = error.get("message", "Unknown API error")
    error_type = error.get("type", "unknown_error")
    status_code = error_response.get("status_code")

    is_retriable = error_type in ["server_error", "rate_limit_exceeded", "timeout"]

    return APIError(
        message=message,
        error_type=error_type,
        status_code=status_code,
        is_retriable=is_retriable,
    )
