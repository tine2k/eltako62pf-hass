"""Custom exceptions for Eltako ESR62PF-IP integration."""


class EltakoError(Exception):
    """Base exception for Eltako integration."""


class EltakoAuthenticationError(EltakoError):
    """Exception raised when authentication fails."""


class EltakoConnectionError(EltakoError):
    """Exception raised when connection to device fails."""


class EltakoAPIError(EltakoError):
    """Exception raised when API returns an error."""


class EltakoTimeoutError(EltakoError):
    """Exception raised when request times out."""


class EltakoInvalidDeviceError(EltakoError):
    """Exception raised when device GUID is invalid."""
