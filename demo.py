#!/usr/bin/env python3
"""
Demonstration script for OVH OpenStack Deployment Automation configuration management.

This script demonstrates:
1. Loading configuration from YAML file
2. Validating configuration
3. Accessing configuration data
4. Using the logging infrastructure
"""

import sys
from pathlib import Path

from config import ConfigurationManager
from utils import setup_logging, get_logger


def main():
    """Main demonstration function."""
    # Set up dummy environment variables for demo
    import os
    os.environ['OS_USERNAME'] = 'demo-user'
    os.environ['OS_PASSWORD'] = 'demo-password'
    os.environ['OS_TENANT_NAME'] = 'demo-tenant'
    
    # Set up logging
    logger = setup_logging(log_level="INFO")
    logger.info("=" * 60)
    logger.info("OVH OpenStack Deployment Configuration Demo")
    logger.info("=" * 60)
    logger.info("Note: Using demo credentials for demonstration purposes")
    
    # Initialize configuration manager
    manager = ConfigurationManager()
    logger.info("\n1. Loading configuration from examples/minimal-config.yaml")
    
    try:
        # Load configuration
        config = manager.load_config('examples/minimal-config.yaml')
        logger.info("✓ Configuration loaded successfully")
        
        # Display configuration summary
        logger.info("\n2. Configuration Summary:")
        logger.info(f"   - Auth URL: {config.auth_url}")
        logger.info(f"   - Region: {config.region}")
        logger.info(f"   - Project: {config.project_name}")
        logger.info(f"   - Instances: {len(config.instances)}")
        logger.info(f"   - Networks: {len(config.networks)}")
        logger.info(f"   - Security Groups: {len(config.security_groups)}")
        logger.info(f"   - Volumes: {len(config.volumes)}")
        
        # Display instance details
        if config.instances:
            logger.info("\n3. Instance Details:")
            for instance in config.instances:
                logger.info(f"   - Name: {instance.name}")
                logger.info(f"     Flavor: {instance.flavor}")
                logger.info(f"     Image: {instance.image}")
                logger.info(f"     Networks: {', '.join(instance.network_ids)}")
                logger.info(f"     Security Groups: {', '.join(instance.security_groups)}")
        
        # Display network details
        if config.networks:
            logger.info("\n4. Network Details:")
            for network in config.networks:
                logger.info(f"   - Name: {network.name}")
                logger.info(f"     External: {network.external}")
                logger.info(f"     Subnets: {len(network.subnets)}")
                for subnet in network.subnets:
                    logger.info(f"       * {subnet.name}: {subnet.cidr}")
        
        # Validate configuration
        logger.info("\n5. Validating configuration...")
        validation_result = manager.validate_config(config)
        
        if validation_result.is_valid:
            logger.info("✓ Configuration is valid!")
        else:
            logger.error("✗ Configuration validation failed:")
            for error in validation_result.errors:
                logger.error(f"   - {error}")
            return 1
        
        # Extract authentication credentials
        logger.info("\n6. Authentication Credentials:")
        auth_creds = manager.get_auth_credentials(config)
        logger.info(f"   - Auth URL: {auth_creds.auth_url}")
        logger.info(f"   - Username: {auth_creds.username}")
        logger.info(f"   - Tenant: {auth_creds.tenant_name}")
        logger.info(f"   - Region: {auth_creds.region}")
        logger.info(f"   - Password: {'*' * len(auth_creds.password)} (hidden)")
        
        logger.info("\n" + "=" * 60)
        logger.info("Demo completed successfully!")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"✗ Configuration file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        logger.exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
