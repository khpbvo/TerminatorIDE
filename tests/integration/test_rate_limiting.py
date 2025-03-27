import time

from terminatoride.utils.error_handling import RateLimitHandler


class TestRateLimiting:
    def test_rate_limiting_over_time(self):
        """Test that rate limiting respects the time window"""
        # Use a very short time window for testing
        handler = RateLimitHandler(max_requests=1, time_window=0.1)

        # First request should be allowed
        assert handler.can_make_request() is True

        # Second request should be denied (rate limited)
        assert handler.can_make_request() is False

        # Wait for time window to expire
        time.sleep(0.2)

        # Now should be allowed again
        assert handler.can_make_request() is True
