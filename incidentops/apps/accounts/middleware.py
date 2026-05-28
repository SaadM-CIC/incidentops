import logging
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class SecurityLoggingMiddleware:
    """Log les accès non autorisés pour audit."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 403:
            logger.warning(
                f"Accès refusé — User: {request.user} | "
                f"URL: {request.path} | "
                f"IP: {request.META.get('REMOTE_ADDR')}"
            )
        return response