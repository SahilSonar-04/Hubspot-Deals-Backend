import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for extraction service domain errors."""
    def __init__(self, message: str, details: dict = None, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class HubspotAPIError(ServiceError):
    """Raised when the HubSpot API returns an unrecoverable error or rate limit exhaustion."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class JobNotFoundError(ServiceError):
    """Raised when a requested extraction job is not found."""
    def __init__(self, job_id: str):
        super().__init__(
            message=f"Extraction job with ID '{job_id}' not found.",
            details={"job_id": job_id},
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvalidPaginationError(ServiceError):
    """Raised when pagination parameters are malformed or invalid."""
    def __init__(self, message: str = "Invalid pagination parameters: 'limit' and 'offset' must be valid integers."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


def custom_exception_handler(exc, context):
    """
    Centralized DRF exception handler mapping custom domain exceptions
    and standard DRF exceptions into consistent, structured JSON error payloads.
    """
    # First invoke DRF's default exception handler to handle standard REST framework errors
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize DRF error response structure
        data = response.data
        if isinstance(data, dict):
            if "detail" in data:
                error_msg = data["detail"]
            elif "error" in data:
                error_msg = data["error"]
            else:
                error_msg = data
        elif isinstance(data, list):
            error_msg = data[0] if data else "An error occurred."
        else:
            error_msg = str(data)

        response.data = {
            "error": error_msg,
            "status_code": response.status_code
        }
        return response

    # Handle custom domain exceptions
    if isinstance(exc, ServiceError):
        logger.warning(f"Domain ServiceError handled: {exc.message} (status={exc.status_code})")
        return Response(
            {
                "error": exc.message,
                "details": exc.details,
                "status_code": exc.status_code
            },
            status=exc.status_code
        )

    if isinstance(exc, ValueError):
        logger.warning(f"ValueError handled: {exc}")
        return Response(
            {
                "error": str(exc),
                "status_code": status.HTTP_400_BAD_REQUEST
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Unhandled 500 server error
    logger.exception(f"Unhandled server exception: {exc}")
    return Response(
        {
            "error": "An internal server error occurred.",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )