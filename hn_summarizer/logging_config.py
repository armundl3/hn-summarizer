"""
Logging configuration for HN Summarizer.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs to stderr.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler (stderr to avoid mixing with stdout output)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set specific logger levels for external libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)


# Performance timing decorator
import time
from functools import wraps


def log_performance(logger: logging.Logger, operation: str):
    """Decorator to log performance timing for functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Starting {operation}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Completed {operation} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed {operation} after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator