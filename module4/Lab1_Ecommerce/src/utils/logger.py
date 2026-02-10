"""
Logging Utilities Module
Centralized logging functions to replace print statements.
Provides consistent, colored output for different log levels.
"""


def log_info(message: str):
    """
    Log an informational message.
    
    Args:
        message: The message to log
    """
    print(f"[INFO] {message}")


def log_success(message: str):
    """
    Log a success message.
    
    Args:
        message: The message to log
    """
    print(f"[SUCCESS] {message}")


def log_error(message: str):
    """
    Log an error message.
    
    Args:
        message: The message to log
    """
    print(f"[ERROR] {message}")


def log_warning(message: str):
    """
    Log a warning message.
    
    Args:
        message: The message to log
    """
    print(f"[WARNING] {message}")


def log_debug(message: str):
    """
    Log a debug message.
    
    Args:
        message: The message to log
    """
    print(f"[DEBUG] {message}")
