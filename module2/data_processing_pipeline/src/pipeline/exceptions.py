class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""


class CleaningError(PipelineError):
    """Raised when text cleaning fails."""


class AnalysisError(PipelineError):
    """Raised when sentiment analysis fails."""


class StorageError(PipelineError):
    """Raised when data storage fails."""
