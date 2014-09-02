class FionaValueError(ValueError):
    """Fiona-specific value errors"""

class DriverError(FionaValueError):
    """Encapsulates unsupported driver and driver mode errors."""

class SchemaError(FionaValueError):
    """When a schema mapping has no properties or no geometry."""

class CRSError(FionaValueError):
    """When a crs mapping has neither init or proj items."""
