#!/usr/bin/env python3
"""
Demonstration script for OVH OpenStack Deployment Automation configuration management.

This script demonstrates:
1. Loading configuration from YAML file
2. Validating configuration
3. Accessing configuration data
4. Using the logging infrastructure
5. Handling both traditional and application credentials
"""

import sys
from pathlib import Path

from config.config_manager import ConfigurationManager
from utils.logger import setup_logging, get_logger


def main():
    """Main demonstration function."""
    # Set up dummy environment variables for demo - traditional credentials
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
        
        # Show application credentials support
        # Check if we have application credential fields in the original config
        # (this is a bit hacky but works for the demo)
        config_dict = {}
        try:
            with open('examples/minimal-config.yaml', 'r') as f:
                import yaml
                config_dict = yaml.safe_load(f)
        except:
            pass
        
        has_app_creds = ('application_credential_id' in config_dict and 
                        'application_credential_secret' in config_dict)
        
        if has_app_creds or auth_creds.application_credential_id:
            logger.info("   - Application Credential ID: Provided")
            logger.info("   - Application Credential Secret: Provided")
            logger.info("   - Using Application Credentials authentication")
        else:
            logger.info("   - Using Traditional Username/Password authentication")
        
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


def demo_application_credentials():
    """Demonstrate application credentials usage with environment variables."""
    # Set up environment variables for application credentials demo
    import os
    os.environ['OS_APPLICATION_CREDENTIAL_ID'] = 'app-cred-id-12345'
    os.environ['OS_APPLICATION_CREDENTIAL_SECRET'] = 'app-cred-secret-67890'
    os.environ['OS_TENANT_NAME'] = 'demo-tenant'
    os.environ['OS_AUTH_URL'] = 'https://auth.cloud.ovh.net/v3'
    os.environ['OS_REGION_NAME'] = 'GRA7'
    
    logger = setup_logging(log_level="INFO")
    logger.info("=" * 60)
    logger.info("Application Credentials Demo")
    logger.info("=" * 60)
    
    # Initialize configuration manager
    manager = ConfigurationManager()
    
    # Load configuration using the auth manager to simulate real usage
    try:
        # This simulates loading credentials from environment variables
        # which is how application credentials are typically used
        from openstack_sdk.auth_manager import AuthenticationManager
        auth_manager = AuthenticationManager()
        auth_creds = auth_manager.load_credentials_from_env()
        
        logger.info("✓ Loaded authentication credentials from environment variables")
        logger.info(f"   - Auth URL: {auth_creds.auth_url}")
        logger.info(f"   - Tenant: {auth_creds.tenant_name}")
        logger.info(f"   - Region: {auth_creds.region}")
        
        if auth_creds.application_credential_id:
            logger.info("✓ Application credentials detected")
            logger.info(f"   - Application Credential ID: {auth_creds.application_credential_id}")
            logger.info(f"   - Application Credential Secret: {'*' * len(auth_creds.application_credential_secret)} (hidden)")
            logger.info("   - Using Application Credentials authentication")
        else:
            logger.info("   - Using Traditional Username/Password authentication")
            
    except Exception as e:
        logger.error(f"Error in application credentials demo: {e}")
        logger.exception(e)


if __name__ == "__main__":
    # Run main demo
    result = main()
    
    # Run application credentials demo
    if result == 0:
        demo_application_credentials()
    
    sys.exit(result)
