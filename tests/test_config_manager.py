"""Unit tests for ConfigurationManager."""

import pytest
import tempfile
import os
from pathlib import Path

from config import ConfigurationManager, ValidationResult


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigurationManager()

    def test_load_yaml_config(self):
        """Test loading YAML configuration file."""
        yaml_content = """
auth_url: "https://auth.cloud.ovh.net/v3"
username: "test-user"
password: "test-pass"
tenant_name: "test-tenant"
region: "GRA7"
project_name: "test-project"

instances:
  - name: "test-instance"
    flavor: "s1-2"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]
    security_groups: ["test-sg"]

networks:
  - name: "test-network"
    subnets:
      - name: "test-subnet"
        cidr: "192.168.1.0/24"

security_groups:
  - name: "test-sg"
    description: "Test security group"
    rules: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            assert config.auth_url == "https://auth.cloud.ovh.net/v3"
            assert config.username == "test-user"
            assert len(config.instances) == 1
            assert config.instances[0].name == "test-instance"
        finally:
            os.unlink(temp_path)

    def test_load_json_config(self):
        """Test loading JSON configuration file."""
        json_content = """{
  "auth_url": "https://auth.cloud.ovh.net/v3",
  "username": "test-user",
  "password": "test-pass",
  "tenant_name": "test-tenant",
  "region": "GRA7",
  "project_name": "test-project",
  "instances": [
    {
      "name": "test-instance",
      "flavor": "s1-2",
      "image": "Ubuntu 22.04",
      "key_name": "test-key",
      "network_ids": ["test-network"],
      "security_groups": ["test-sg"]
    }
  ],
  "networks": [
    {
      "name": "test-network",
      "subnets": [
        {
          "name": "test-subnet",
          "cidr": "192.168.1.0/24"
        }
      ]
    }
  ],
  "security_groups": [
    {
      "name": "test-sg",
      "description": "Test security group",
      "rules": []
    }
  ]
}"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            assert config.auth_url == "https://auth.cloud.ovh.net/v3"
            assert config.username == "test-user"
            assert len(config.instances) == 1
        finally:
            os.unlink(temp_path)

    def test_environment_variable_substitution(self):
        """Test environment variable substitution in configuration."""
        os.environ['TEST_USERNAME'] = 'env-user'
        os.environ['TEST_PASSWORD'] = 'env-pass'

        yaml_content = """
auth_url: "https://auth.cloud.ovh.net/v3"
username: "${TEST_USERNAME}"
password: "${TEST_PASSWORD}"
tenant_name: "test-tenant"
region: "GRA7"
project_name: "test-project"

instances:
  - name: "test-instance"
    flavor: "s1-2"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]

networks:
  - name: "test-network"
    subnets:
      - name: "test-subnet"
        cidr: "192.168.1.0/24"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            assert config.username == "env-user"
            assert config.password == "env-pass"
        finally:
            os.unlink(temp_path)
            del os.environ['TEST_USERNAME']
            del os.environ['TEST_PASSWORD']

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        yaml_content = """
auth_url: "https://auth.cloud.ovh.net/v3"
username: "test-user"
password: "test-pass"
tenant_name: "test-tenant"
region: "GRA7"
project_name: "test-project"

instances:
  - name: "test-instance"
    flavor: "s1-2"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]
    security_groups: ["test-sg"]

networks:
  - name: "test-network"
    subnets:
      - name: "test-subnet"
        cidr: "192.168.1.0/24"

security_groups:
  - name: "test-sg"
    description: "Test security group"
    rules: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            result = self.manager.validate_config(config)
            assert result.is_valid
            assert len(result.errors) == 0
        finally:
            os.unlink(temp_path)

    def test_validate_missing_auth_url(self):
        """Test validation fails when auth_url is missing."""
        yaml_content = """
auth_url: ""
username: "test-user"
password: "test-pass"
tenant_name: "test-tenant"
region: "GRA7"
project_name: "test-project"

instances:
  - name: "test-instance"
    flavor: "s1-2"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]

networks:
  - name: "test-network"
    subnets:
      - name: "test-subnet"
        cidr: "192.168.1.0/24"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            result = self.manager.validate_config(config)
            assert not result.is_valid
            assert any("auth_url" in error for error in result.errors)
        finally:
            os.unlink(temp_path)

    def test_validate_duplicate_instance_names(self):
        """Test validation fails with duplicate instance names."""
        yaml_content = """
auth_url: "https://auth.cloud.ovh.net/v3"
username: "test-user"
password: "test-pass"
tenant_name: "test-tenant"
region: "GRA7"
project_name: "test-project"

instances:
  - name: "duplicate-name"
    flavor: "s1-2"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]
  - name: "duplicate-name"
    flavor: "s1-4"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]

networks:
  - name: "test-network"
    subnets:
      - name: "test-subnet"
        cidr: "192.168.1.0/24"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            result = self.manager.validate_config(config)
            assert not result.is_valid
            assert any("Duplicate instance name" in error for error in result.errors)
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_cidr(self):
        """Test validation fails with invalid CIDR notation."""
        yaml_content = """
auth_url: "https://auth.cloud.ovh.net/v3"
username: "test-user"
password: "test-pass"
tenant_name: "test-tenant"
region: "GRA7"
project_name: "test-project"

instances:
  - name: "test-instance"
    flavor: "s1-2"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]

networks:
  - name: "test-network"
    subnets:
      - name: "test-subnet"
        cidr: "invalid-cidr"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            result = self.manager.validate_config(config)
            assert not result.is_valid
            assert any("Invalid CIDR" in error for error in result.errors)
        finally:
            os.unlink(temp_path)

    def test_validate_security_group_rule(self):
        """Test validation of security group rules."""
        yaml_content = """
auth_url: "https://auth.cloud.ovh.net/v3"
username: "test-user"
password: "test-pass"
tenant_name: "test-tenant"
region: "GRA7"
project_name: "test-project"

instances:
  - name: "test-instance"
    flavor: "s1-2"
    image: "Ubuntu 22.04"
    key_name: "test-key"
    network_ids: ["test-network"]
    security_groups: ["test-sg"]

networks:
  - name: "test-network"
    subnets:
      - name: "test-subnet"
        cidr: "192.168.1.0/24"

security_groups:
  - name: "test-sg"
    description: "Test security group"
    rules:
      - direction: "ingress"
        protocol: "tcp"
        port_range_min: 22
        port_range_max: 22
        remote_ip_prefix: "0.0.0.0/0"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = self.manager.load_config(temp_path)
            result = self.manager.validate_config(config)
            assert result.is_valid
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.manager.load_config('non-existent-file.yaml')

    def test_unsupported_file_format(self):
        """Test error handling for unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                self.manager.load_config(temp_path)
        finally:
            os.unlink(temp_path)
