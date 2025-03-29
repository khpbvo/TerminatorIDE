"""
Tests for the RateLimitHandler functionality.
"""

import time

from terminatoride.utils.error_handling import RateLimitHandler


class TestRateLimitHandler:
    """Test the RateLimitHandler class."""

    def test_init(self):
        """Test initialization with different parameters."""
        # Default initialization
        handler = RateLimitHandler()
        assert handler.max_requests == 50
        assert handler.time_window == 60
        assert len(handler.request_timestamps) == 0
        assert handler.request_count == 0

        # Custom initialization
        handler = RateLimitHandler(max_requests=100, time_window=30)
        assert handler.max_requests == 100
        assert handler.time_window == 30

    def test_can_make_request_basic(self):
        """Test basic request acceptance."""
        handler = RateLimitHandler(max_requests=3, time_window=60)

        # First request should be allowed
        assert handler.can_make_request() is True
        assert len(handler.request_timestamps) == 1
        assert handler.request_count == 1

        # Second request should be allowed
        assert handler.can_make_request() is True
        assert len(handler.request_timestamps) == 2
        assert handler.request_count == 2

        # Third request should be allowed
        assert handler.can_make_request() is True
        assert len(handler.request_timestamps) == 3
        assert handler.request_count == 3

        # Fourth request should be denied
        assert handler.can_make_request() is False
        assert len(handler.request_timestamps) == 3  # Should not increase
        assert handler.request_count == 3  # Should not increase

    def test_time_window_expiration(self):
        """Test that timestamps older than the time window are removed."""
        handler = RateLimitHandler(
            max_requests=2, time_window=0.1
        )  # Very short window for testing

        # First request
        assert handler.can_make_request() is True

        # Simulate time passing
        time.sleep(0.15)  # Longer than the time window

        # Second request - should remove the first request's timestamp
        assert handler.can_make_request() is True
        assert len(handler.request_timestamps) == 1  # Only the new request

        # Third request - should be allowed since the first one expired
        assert handler.can_make_request() is True
        assert len(handler.request_timestamps) == 2

    def test_time_until_next_request(self):
        """Test calculating the time until next request is allowed."""
        handler = RateLimitHandler(max_requests=1, time_window=0.5)

        # Make a request
        assert handler.can_make_request() is True

        # Check time until next request
        wait_time = handler.time_until_next_request()
        assert wait_time > 0  # Should be positive
        assert wait_time <= 0.5  # Should be less than or equal to the time window

        # Wait for the time window to expire
        time.sleep(0.6)

        # Time until next request should now be 0
        wait_time = handler.time_until_next_request()
        assert wait_time == 0.0

    def test_rapid_requests(self):
        """Test behavior with rapid successive requests."""
        handler = RateLimitHandler(max_requests=5, time_window=0.5)

        # Make multiple requests rapidly
        for _ in range(5):
            assert handler.can_make_request() is True

        # The next request should be denied
        assert handler.can_make_request() is False

        # Wait a bit but not long enough for all requests to expire
        time.sleep(0.3)

        # Should still be denied
        assert handler.can_make_request() is False

        # Wait for all requests to expire
        time.sleep(0.3)

        # Now should be allowed again
        assert handler.can_make_request() is True

    def test_request_count_persistence(self):
        """Test that request_count persists even when timestamps are removed."""
        handler = RateLimitHandler(max_requests=5, time_window=0.1)

        # Make some requests
        for _ in range(3):
            assert handler.can_make_request() is True

        # Initial count
        assert handler.request_count == 3

        # Wait for timestamps to expire
        time.sleep(0.2)

        # Make another request
        assert handler.can_make_request() is True

        # Count should increment even though old timestamps were removed
        assert handler.request_count == 4
