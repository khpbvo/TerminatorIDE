from terminatoride.utils.error_handling import (RateLimitHandler,
                                                handle_api_error)


class TestErrorHandling:
    def test_handle_api_error(self):
        """Test API error handling"""
        error_response = {"error": {"message": "Test error", "type": "api_error"}}
        result = handle_api_error(error_response)
        assert "Test error" in result.message
        assert result.error_type == "api_error"

    def test_rate_limit_handler_init(self):
        """Test rate limiting initialization"""
        handler = RateLimitHandler(max_requests=10, time_window=60)
        assert handler.max_requests == 10
        assert handler.time_window == 60
        assert len(handler.request_timestamps) == 0

    def test_rate_limit_handler_can_make_request(self):
        """Test rate limiting functionality"""
        handler = RateLimitHandler(max_requests=2, time_window=60)

        # First request should be allowed
        assert handler.can_make_request() is True
        assert len(handler.request_timestamps) == 1

        # Second request should be allowed
        assert handler.can_make_request() is True
        assert len(handler.request_timestamps) == 2

        # Third request should be rate limited
        assert handler.can_make_request() is False
        assert len(handler.request_timestamps) == 2
