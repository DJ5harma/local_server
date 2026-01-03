"""
Custom exceptions for the SV30 Test System HMI server.
"""


class SV30Error(Exception):
    """Base exception for all SV30 system errors"""
    pass


class DataGenerationError(SV30Error):
    """Raised when data generation fails"""
    pass


class TestStateError(SV30Error):
    """Raised when test state operations are invalid"""
    pass


class BackendConnectionError(SV30Error):
    """Raised when backend connection fails"""
    pass


class ConfigurationError(SV30Error):
    """Raised when configuration is invalid"""
    pass

