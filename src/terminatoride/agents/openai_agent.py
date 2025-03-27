from ..utils.error_handling import RateLimitHandler


class OpenAIAgent:
    def __init__(self):
        """Initialize the OpenAI agent with rate limiting."""
        self.rate_limiter = RateLimitHandler(max_requests=50, time_window=60)

    async def generate_response(self, prompt: str) -> str:
        """Generate a response to the prompt.

        Args:
            prompt: The prompt to generate a response to.

        Returns:
            The generated response.
        """
        # In a real implementation, this would call the OpenAI API
        # For the test, we'll just return a simple response
        # and track it with the rate limiter
        self.rate_limiter.can_make_request()  # This increments request_count
        return f"Response to: {prompt}"
