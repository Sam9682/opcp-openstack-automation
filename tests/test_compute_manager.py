"""Unit tests for compute instance manager."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from openstack.compute.v2.server import Server
from openstack.compute.v2.flavor import Flavor
from openstack.compute.v2.image import Image
from openstack.network.v2.network import Network
from openstack.network.v2.security_group import SecurityGroup
from openstack.exceptions import SDKException

from openstack_sdk.compute_manager import ComputeManager, ComputeError
from config.models import InstanceSpec


@pytest.fixture
def mock_connection():
    """Create a mock OpenStack connection."""
    conn = Mock()
    conn.compute = Mock()
    conn.network = Mock()
    return conn


@pytest.fixture
def compute_manager(mock_connection):
    """Create a ComputeManager instance with mock connection."""
    return ComputeManager(mock_connection)


@pytest.fixture
def sample_instance_spec():
    """Create a sample instance specification."""
    return InstanceSpec(
        name="test-instance",
        flavor="s1-4",
        image="Ubuntu 22.04",
        key_name="test-key",
        network_ids=["net-123"],
        security_groups=["default"],
        user_data="#!/bin/bash\necho 'Hello World'",
        metadata={"project": "test", "environment": "dev"}
    )


class TestComputeManager:
    """Test cases for ComputeManager."""
    
    def test_create_instance_success(self, compute_manager, mock_connection, sample_instance_spec):
        """Test successful instance creation."""
        # Mock flavor lookup
        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-123"
        mock_connection.compute.find_flavor.return_value = mock_flavor
        
        # Mock image lookup
        mock_image = Mock(spec=Image)
        mock_image.id = "image-456"
        mock_connection.compute.find_image.return_value = mock_image
        
        # Mock network validation
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        mock_connection.network.get_network.return_value = mock_network
        
        # Mock security group validation
        mock_sg = Mock(spec=SecurityGroup)
        mock_sg.name = "default"
        mock_connection.network.security_groups.return_value = [mock_sg]
        
        # Mock instance creation
        mock_instance = Mock(spec=Server)
        mock_instance.id = "instance-789"
        mock_instance.name = "test-instance"
        mock_instance.status = "BUILD"
        mock_connection.compute.create_server.return_value = mock_instance
        
        # Create instance
        result = compute_manager.create_instance(sample_instance_spec)
        
        # Verify result
        assert result == mock_instance
        assert result.id == "instance-789"
        
        # Verify create_server was called with correct parameters
        mock_connection.compute.create_server.assert_called_once()
        call_args = mock_connection.compute.create_server.call_args[1]
        assert call_args['name'] == "test-instance"
        assert call_args['flavor_id'] == "flavor-123"
        assert call_args['image_id'] == "image-456"
        assert call_args['key_name'] == "test-key"
        assert call_args['networks'] == [{'uuid': 'net-123'}]
        assert call_args['security_groups'] == [{'name': 'default'}]
        assert call_args['user_data'] == "#!/bin/bash\necho 'Hello World'"
        assert call_args['metadata'] == {"project": "test", "environment": "dev"}
    
    def test_create_instance_flavor_not_found(self, compute_manager, mock_connection, sample_instance_spec):
        """Test instance creation fails when flavor not found."""
        # Mock flavor lookup to return None
        mock_connection.compute.find_flavor.return_value = None
        
        # Attempt to create instance
        with pytest.raises(ComputeError) as exc_info:
            compute_manager.create_instance(sample_instance_spec)
        
        assert "Flavor 's1-4' not found" in str(exc_info.value)
    
    def test_create_instance_image_not_found(self, compute_manager, mock_connection, sample_instance_spec):
        """Test instance creation fails when image not found."""
        # Mock flavor lookup
        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-123"
        mock_connection.compute.find_flavor.return_value = mock_flavor
        
        # Mock image lookup to return None
        mock_connection.compute.find_image.return_value = None
        
        # Attempt to create instance
        with pytest.raises(ComputeError) as exc_info:
            compute_manager.create_instance(sample_instance_spec)
        
        assert "Image 'Ubuntu 22.04' not found" in str(exc_info.value)
    
    def test_create_instance_no_networks(self, compute_manager, mock_connection):
        """Test instance creation fails when no networks specified."""
        # Create instance spec without networks
        instance_spec = InstanceSpec(
            name="test-instance",
            flavor="s1-4",
            image="Ubuntu 22.04",
            key_name="test-key",
            network_ids=[]
        )
        
        # Mock flavor and image lookup
        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-123"
        mock_connection.compute.find_flavor.return_value = mock_flavor
        
        mock_image = Mock(spec=Image)
        mock_image.id = "image-456"
        mock_connection.compute.find_image.return_value = mock_image
        
        # Attempt to create instance
        with pytest.raises(ComputeError) as exc_info:
            compute_manager.create_instance(instance_spec)
        
        assert "requires at least one network" in str(exc_info.value)
    
    def test_create_instance_network_not_found(self, compute_manager, mock_connection, sample_instance_spec):
        """Test instance creation fails when network doesn't exist."""
        # Mock flavor and image lookup
        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-123"
        mock_connection.compute.find_flavor.return_value = mock_flavor
        
        mock_image = Mock(spec=Image)
        mock_image.id = "image-456"
        mock_connection.compute.find_image.return_value = mock_image
        
        # Mock network validation to return None
        mock_connection.network.get_network.return_value = None
        
        # Attempt to create instance
        with pytest.raises(ComputeError) as exc_info:
            compute_manager.create_instance(sample_instance_spec)
        
        assert "Network 'net-123' not found" in str(exc_info.value)
    
    def test_create_instance_security_group_not_found(self, compute_manager, mock_connection, sample_instance_spec):
        """Test instance creation fails when security group doesn't exist."""
        # Mock flavor and image lookup
        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-123"
        mock_connection.compute.find_flavor.return_value = mock_flavor
        
        mock_image = Mock(spec=Image)
        mock_image.id = "image-456"
        mock_connection.compute.find_image.return_value = mock_image
        
        # Mock network validation
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        mock_connection.network.get_network.return_value = mock_network
        
        # Mock security group validation to return empty list
        mock_connection.network.security_groups.return_value = []
        
        # Attempt to create instance
        with pytest.raises(ComputeError) as exc_info:
            compute_manager.create_instance(sample_instance_spec)
        
        assert "Security group 'default' not found" in str(exc_info.value)
    
    def test_create_compute_instances_duplicate_names(self, compute_manager):
        """Test instance creation fails with duplicate names."""
        instance_specs = [
            InstanceSpec(
                name="duplicate-name",
                flavor="s1-4",
                image="Ubuntu 22.04",
                key_name="test-key",
                network_ids=["net-123"]
            ),
            InstanceSpec(
                name="duplicate-name",
                flavor="s1-4",
                image="Ubuntu 22.04",
                key_name="test-key",
                network_ids=["net-123"]
            )
        ]
        
        with pytest.raises(ComputeError) as exc_info:
            compute_manager.create_compute_instances(instance_specs)
        
        assert "Duplicate instance names found" in str(exc_info.value)
        assert "duplicate-name" in str(exc_info.value)
    
    def test_wait_for_instances_active_success(self, compute_manager, mock_connection):
        """Test waiting for instances to become ACTIVE."""
        # Create mock instances
        mock_instance1 = Mock(spec=Server)
        mock_instance1.id = "instance-1"
        mock_instance1.name = "test-1"
        mock_instance1.status = "BUILD"
        
        mock_instance2 = Mock(spec=Server)
        mock_instance2.id = "instance-2"
        mock_instance2.name = "test-2"
        mock_instance2.status = "BUILD"
        
        # Mock get_server to return ACTIVE status
        active_instance1 = Mock(spec=Server)
        active_instance1.id = "instance-1"
        active_instance1.name = "test-1"
        active_instance1.status = "ACTIVE"
        
        active_instance2 = Mock(spec=Server)
        active_instance2.id = "instance-2"
        active_instance2.name = "test-2"
        active_instance2.status = "ACTIVE"
        
        mock_connection.compute.get_server.side_effect = [
            active_instance1,
            active_instance2
        ]
        
        # Wait for instances
        compute_manager._wait_for_instances_active([mock_instance1, mock_instance2])
        
        # Verify get_server was called
        assert mock_connection.compute.get_server.call_count == 2
    
    def test_wait_for_instances_active_error_state(self, compute_manager, mock_connection):
        """Test waiting for instances fails when instance enters ERROR state."""
        # Create mock instance
        mock_instance = Mock(spec=Server)
        mock_instance.id = "instance-1"
        mock_instance.name = "test-1"
        mock_instance.status = "BUILD"
        
        # Mock get_server to return ERROR status
        error_instance = Mock(spec=Server)
        error_instance.id = "instance-1"
        error_instance.name = "test-1"
        error_instance.status = "ERROR"
        error_instance.fault = {"message": "No valid host found"}
        
        mock_connection.compute.get_server.return_value = error_instance
        
        # Wait for instances should raise error
        with pytest.raises(ComputeError) as exc_info:
            compute_manager._wait_for_instances_active([mock_instance])
        
        assert "entered ERROR state" in str(exc_info.value)
        assert "No valid host found" in str(exc_info.value)
    
    def test_wait_for_instances_active_timeout(self, compute_manager, mock_connection):
        """Test waiting for instances times out."""
        # Set short timeout for testing
        compute_manager.INSTANCE_ACTIVE_TIMEOUT = 1
        compute_manager.POLLING_INTERVAL = 0.5
        
        # Create mock instance
        mock_instance = Mock(spec=Server)
        mock_instance.id = "instance-1"
        mock_instance.name = "test-1"
        mock_instance.status = "BUILD"
        
        # Mock get_server to always return BUILD status
        build_instance = Mock(spec=Server)
        build_instance.id = "instance-1"
        build_instance.name = "test-1"
        build_instance.status = "BUILD"
        
        mock_connection.compute.get_server.return_value = build_instance
        
        # Wait for instances should timeout
        with pytest.raises(ComputeError) as exc_info:
            compute_manager._wait_for_instances_active([mock_instance])
        
        assert "Timeout waiting for instances" in str(exc_info.value)
    
    def test_flavor_caching(self, compute_manager, mock_connection):
        """Test that flavor lookups are cached."""
        # Mock flavor lookup
        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-123"
        mock_connection.compute.find_flavor.return_value = mock_flavor
        
        # First lookup
        flavor_id1 = compute_manager._get_flavor_id("s1-4")
        assert flavor_id1 == "flavor-123"
        
        # Second lookup should use cache
        flavor_id2 = compute_manager._get_flavor_id("s1-4")
        assert flavor_id2 == "flavor-123"
        
        # Verify find_flavor was only called once
        mock_connection.compute.find_flavor.assert_called_once_with("s1-4")
    
    def test_image_caching(self, compute_manager, mock_connection):
        """Test that image lookups are cached."""
        # Mock image lookup
        mock_image = Mock(spec=Image)
        mock_image.id = "image-456"
        mock_connection.compute.find_image.return_value = mock_image
        
        # First lookup
        image_id1 = compute_manager._get_image_id("Ubuntu 22.04")
        assert image_id1 == "image-456"
        
        # Second lookup should use cache
        image_id2 = compute_manager._get_image_id("Ubuntu 22.04")
        assert image_id2 == "image-456"
        
        # Verify find_image was only called once
        mock_connection.compute.find_image.assert_called_once_with("Ubuntu 22.04")
    
    def test_create_instance_without_optional_fields(self, compute_manager, mock_connection):
        """Test instance creation without optional fields (user_data, metadata, security_groups)."""
        # Create instance spec without optional fields
        instance_spec = InstanceSpec(
            name="minimal-instance",
            flavor="s1-2",
            image="Debian 11",
            key_name="test-key",
            network_ids=["net-123"]
        )
        
        # Mock flavor and image lookup
        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-123"
        mock_connection.compute.find_flavor.return_value = mock_flavor
        
        mock_image = Mock(spec=Image)
        mock_image.id = "image-456"
        mock_connection.compute.find_image.return_value = mock_image
        
        # Mock network validation
        mock_network = Mock(spec=Network)
        mock_network.id = "net-123"
        mock_connection.network.get_network.return_value = mock_network
        
        # Mock instance creation
        mock_instance = Mock(spec=Server)
        mock_instance.id = "instance-789"
        mock_instance.name = "minimal-instance"
        mock_instance.status = "BUILD"
        mock_connection.compute.create_server.return_value = mock_instance
        
        # Create instance
        result = compute_manager.create_instance(instance_spec)
        
        # Verify result
        assert result == mock_instance
        
        # Verify create_server was called without optional fields
        call_args = mock_connection.compute.create_server.call_args[1]
        assert 'security_groups' not in call_args
        assert 'user_data' not in call_args
        assert 'metadata' not in call_args
    
    def test_get_instance_by_name(self, compute_manager, mock_connection):
        """Test getting instance by name."""
        mock_instance = Mock(spec=Server)
        mock_instance.id = "instance-123"
        mock_instance.name = "test-instance"
        
        mock_connection.compute.servers.return_value = [mock_instance]
        
        result = compute_manager.get_instance_by_name("test-instance")
        
        assert result == mock_instance
        mock_connection.compute.servers.assert_called_once_with(name="test-instance")
    
    def test_list_instances(self, compute_manager, mock_connection):
        """Test listing all instances."""
        mock_instances = [
            Mock(spec=Server, id="instance-1", name="test-1"),
            Mock(spec=Server, id="instance-2", name="test-2")
        ]
        
        mock_connection.compute.servers.return_value = mock_instances
        
        result = compute_manager.list_instances()
        
        assert result == mock_instances
        assert len(result) == 2
    
    def test_delete_instance(self, compute_manager, mock_connection):
        """Test deleting an instance."""
        result = compute_manager.delete_instance("instance-123")
        
        assert result is True
        mock_connection.compute.delete_server.assert_called_once_with("instance-123")
    
    def test_delete_instance_failure(self, compute_manager, mock_connection):
        """Test delete instance handles errors."""
        mock_connection.compute.delete_server.side_effect = SDKException("Delete failed")
        
        result = compute_manager.delete_instance("instance-123")
        
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
