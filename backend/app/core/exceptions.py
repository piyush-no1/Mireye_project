class AquaTraceException(Exception):
    """Base exception for AquaTrace platform."""
    pass

class GeocodeNotFoundException(AquaTraceException):
    """Raised when geocoding fails to resolve a location."""
    def __init__(self, query: str):
        super().__init__(f"No geocoding result found for query: '{query}'")
        self.query = query

class HydrologyResolutionException(AquaTraceException):
    """Raised when USGS COMID resolution or flowline tracing fails."""
    def __init__(self, message: str):
        super().__init__(message)

class ExternalAPIException(AquaTraceException):
    """Raised when an external REST API fails after retries."""
    def __init__(self, service_name: str, message: str, status_code: int | None = None):
        super().__init__(f"[{service_name}] Error (status={status_code}): {message}")
        self.service_name = service_name
        self.status_code = status_code
