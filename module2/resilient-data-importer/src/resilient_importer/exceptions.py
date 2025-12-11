class ImporterError(Exception):
    """Base exception for importer errors."""
    pass

class InvalidCSVError(ImportError):
    """Raised when the input data is invalid."""
    pass

class FileMissingError(ImportError):
    """Raised when a required column is missing from the input data."""
    pass

class EmptyFileError(ImportError):
    """Raised when there is an issue with the importer's configuration."""
    pass
