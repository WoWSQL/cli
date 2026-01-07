"""Custom exceptions for WoWSQL CLI."""


class WoWSQLError(Exception):
    """Base exception for WoWSQL CLI errors."""
    pass


class AuthenticationError(WoWSQLError):
    """Authentication-related errors."""
    pass


class APIError(WoWSQLError):
    """API request errors."""
    pass


class ConfigurationError(WoWSQLError):
    """Configuration-related errors."""
    pass


class MigrationError(WoWSQLError):
    """Migration-related errors."""
    pass


class LocalDevError(WoWSQLError):
    """Local development environment errors."""
    pass

