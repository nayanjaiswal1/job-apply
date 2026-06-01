class AgentError(Exception):
    pass


class TransientError(AgentError):
    """Retryable — network blip, rate limit, upstream timeout."""


class PermanentError(AgentError):
    """Not retryable — bad input, auth failure, logic error."""


class HumanReviewNeeded(AgentError):
    """Pause graph, fire HITL interrupt."""


class RateLimited(TransientError):
    """Provider-level rate limit. Retried with backoff."""


class UpstreamUnavailable(TransientError):
    """Third-party service is down. Retried with backoff."""
