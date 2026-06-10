#!/bin/bash
# Script to set up environment variables for application credentials

echo "Setting up environment variables for application credentials..."

# Set the application credentials environment variables
export OS_AUTH_TYPE=v3applicationcredential
export OS_AUTH_URL=https://keystone.demo.bmp.ovhgoldorack.ovh/v3
export OS_IDENTITY_API_VERSION=3
export OS_REGION_NAME="demo"
export OS_INTERFACE=public
export OS_APPLICATION_CREDENTIAL_ID=your_id
export OS_APPLICATION_CREDENTIAL_SECRET=your_secret

echo "Environment variables set!"
echo "You can now run:"
echo "  python examples/app_cred_example.py"
echo ""
echo "To verify the environment variables:"
echo "  env | grep OS_"