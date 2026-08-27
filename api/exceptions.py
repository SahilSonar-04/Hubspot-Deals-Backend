class ServiceError(Exception):
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class HubspotAPIError(ServiceError):
    """Raised when the HubSpot API returns an unrecoverable error."""
    pass