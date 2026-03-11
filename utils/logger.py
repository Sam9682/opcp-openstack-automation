"""Logging infrastructure for deployment operations."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging infrastructure for deployment operations.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
        log_format: Optional custom log format
        
    Returns:
        Configured logger instance
    """
    # Default log format
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger('ovh_openstack_deployment')
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = 'ovh_openstack_deployment') -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class DeploymentLogger:
    """Logger wrapper with deployment-specific methods."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize deployment logger.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
    
    def log_deployment_start(self, deployment_id: str, config_summary: str):
        """Log deployment start."""
        self.logger.info(f"Starting deployment {deployment_id}")
        self.logger.info(f"Configuration: {config_summary}")
    
    def log_deployment_complete(self, deployment_id: str, success: bool, duration: float):
        """Log deployment completion."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Deployment {deployment_id} completed with status: {status}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
    
    def log_authentication_attempt(self, auth_url: str, username: str):
        """Log authentication attempt (without password)."""
        self.logger.info(f"Attempting authentication to {auth_url} as user {username}")
    
    def log_authentication_success(self):
        """Log successful authentication."""
        self.logger.info("Authentication successful")
    
    def log_authentication_failure(self, error: str):
        """Log authentication failure."""
        self.logger.error(f"Authentication failed: {error}")
    
    def log_resource_creation(self, resource_type: str, resource_name: str):
        """Log resource creation."""
        self.logger.info(f"Creating {resource_type}: {resource_name}")
    
    def log_resource_created(self, resource_type: str, resource_name: str, resource_id: str):
        """Log successful resource creation."""
        self.logger.info(f"Created {resource_type} '{resource_name}' with ID: {resource_id}")
    
    def log_resource_creation_failed(self, resource_type: str, resource_name: str, error: str):
        """Log resource creation failure."""
        self.logger.error(f"Failed to create {resource_type} '{resource_name}': {error}")
    
    def log_resource_deletion(self, resource_type: str, resource_id: str):
        """Log resource deletion."""
        self.logger.info(f"Deleting {resource_type} with ID: {resource_id}")
    
    def log_resource_deleted(self, resource_type: str, resource_id: str):
        """Log successful resource deletion."""
        self.logger.info(f"Deleted {resource_type} with ID: {resource_id}")
    
    def log_resource_deletion_failed(self, resource_type: str, resource_id: str, error: str):
        """Log resource deletion failure."""
        self.logger.error(f"Failed to delete {resource_type} with ID {resource_id}: {error}")
    
    def log_rollback_start(self, deployment_id: str):
        """Log rollback start."""
        self.logger.warning(f"Starting rollback for deployment {deployment_id}")
    
    def log_rollback_complete(self, deployment_id: str, orphaned_resources: list):
        """Log rollback completion."""
        if orphaned_resources:
            self.logger.warning(f"Rollback completed with {len(orphaned_resources)} orphaned resources")
            for resource in orphaned_resources:
                self.logger.warning(f"Orphaned resource: {resource}")
        else:
            self.logger.info(f"Rollback completed successfully for deployment {deployment_id}")
    
    def log_validation_start(self):
        """Log validation start."""
        self.logger.info("Starting configuration validation")
    
    def log_validation_result(self, is_valid: bool, errors: list):
        """Log validation result."""
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error(f"Configuration validation failed with {len(errors)} errors:")
            for error in errors:
                self.logger.error(f"  - {error}")
    
    def log_error(self, message: str, exception: Optional[Exception] = None):
        """Log error with optional exception."""
        self.logger.error(message)
        if exception:
            self.logger.exception(exception)
