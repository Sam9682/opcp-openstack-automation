"""Unit tests for volume_manager module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from openstack.exceptions import SDKException

from openstack_sdk.volume_manager import VolumeManager, VolumeError
from config.models import VolumeSpec


@pytest.fixture
def mock_connection():
    """Create a mock OpenStack connection."""
    conn = Mock()
    conn.block_storage = Mock()
    conn.compute = Mock()
    return conn


@pytest.fixture
def volume_manager(mock_connection):
    """Create a VolumeManager instance with mock connection."""
    return VolumeManager(mock_connection)


@pytest.fixture
def mock_volume():
    """Create a mock Volume object."""
    volume = Mock()
    volume.id = "vol-123"
    volume.name = "test-volume"
    volume.size = 100
    volume.status = "available"
    volume.volume_type = "classic"
    return volume


@pytest.fixture
def mock_instance():
    """Create a mock Server object."""
    instance = Mock()
    instance.id = "inst-123"
    instance.name = "test-instance"
    instance.status = "ACTIVE"
    return instance


class TestVolumeManagerInit:
    """Tests for VolumeManager initialization."""
    
    def test_init_with_connection(self, mock_connection):
        """Test VolumeManager initialization with connection."""
        manager = VolumeManager(mock_connection)
        assert manager.conn == mock_connection
        assert manager.logger is not None
    
    def test_init_with_custom_logger(self, mock_connection):
        """Test VolumeManager initialization with custom logger."""
        custom_logger = Mock()
        manager = VolumeManager(mock_connection, logger=custom_logger)
        assert manager.logger == custom_logger


class TestCreateAndAttachVolumes:
    """Tests for create_and_attach_volumes method."""
    
    def test_create_volumes_empty_list(self, volume_manager):
        """Test creating volumes with empty list."""
        result = volume_manager.create_and_attach_volumes([], {})
        assert result == []
    
    def test_create_single_volume_without_attachment(
        self, volume_manager, mock_connection, mock_volume
    ):
        """Test creating a single volume without attachment."""
        volume_spec = VolumeSpec(
            name="test-volume",
            size=100,
            volume_type="classic"
        )
        
        # Mock volume creation and status polling
        mock_connection.block_storage.create_volume.return_value = mock_volume
        mock_connection.block_storage.get_volume.return_value = mock_volume
        
        result = volume_manager.create_and_attach_volumes([volume_spec], {})
        
        assert len(result) == 1
        assert result[0] == mock_volume
        mock_connection.block_storage.create_volume.assert_called_once()
    
    def test_create_volume_with_attachment(
        self, volume_manager, mock_connection, mock_volume, mock_instance
    ):
        """Test creating a volume and attaching it to an instance."""
        volume_spec = VolumeSpec(
            name="test-volume",
            size=100,
            volume_type="classic",
            attach_to="test-instance"
        )
        
        instances = {"test-instance": mock_instance}
        
        # Mock volume creation
        mock_connection.block_storage.create_volume.return_value = mock_volume
        
        # Mock volume status polling - first available, then in-use
        available_volume = Mock()
        available_volume.id = "vol-123"
        available_volume.status = "available"
        
        in_use_volume = Mock()
        in_use_volume.id = "vol-123"
        in_use_volume.status = "in-use"
        
        mock_connection.block_storage.get_volume.side_effect = [
            available_volume,  # Wait for available
            in_use_volume      # Verify in-use
        ]
        
        # Mock attachment
        mock_attachment = Mock()
        mock_attachment.id = "attach-123"
        mock_connection.compute.create_volume_attachment.return_value = mock_attachment
        
        result = volume_manager.create_and_attach_volumes([volume_spec], instances)
        
        assert len(result) == 1
        mock_connection.compute.create_volume_attachment.assert_called_once()
    
    def test_create_bootable_volume(self, volume_manager, mock_connection, mock_volume):
        """Test creating a bootable volume with image_id."""
        volume_spec = VolumeSpec(
            name="boot-volume",
            size=50,
            volume_type="high-speed",
            bootable=True,
            image_id="img-123"
        )
        
        mock_connection.block_storage.create_volume.return_value = mock_volume
        mock_connection.block_storage.get_volume.return_value = mock_volume
        
        result = volume_manager.create_and_attach_volumes([volume_spec], {})
        
        assert len(result) == 1
        call_args = mock_connection.block_storage.create_volume.call_args
        assert call_args[1]['bootable'] is True
        assert call_args[1]['imageRef'] == "img-123"
    
    def test_create_multiple_volumes(
        self, volume_manager, mock_connection, mock_volume
    ):
        """Test creating multiple volumes."""
        volume_specs = [
            VolumeSpec(name="volume-1", size=100, volume_type="classic"),
            VolumeSpec(name="volume-2", size=200, volume_type="high-speed"),
        ]
        
        mock_connection.block_storage.create_volume.return_value = mock_volume
        mock_connection.block_storage.get_volume.return_value = mock_volume
        
        result = volume_manager.create_and_attach_volumes(volume_specs, {})
        
        assert len(result) == 2
        assert mock_connection.block_storage.create_volume.call_count == 2


class TestValidateVolumeSpec:
    """Tests for _validate_volume_spec method."""
    
    def test_validate_positive_size(self, volume_manager):
        """Test validation accepts positive integer size."""
        volume_spec = VolumeSpec(name="test", size=100, volume_type="classic")
        # Should not raise
        volume_manager._validate_volume_spec(volume_spec, {})
    
    def test_validate_zero_size_fails(self, volume_manager):
        """Test validation rejects zero size."""
        volume_spec = VolumeSpec(name="test", size=0, volume_type="classic")
        with pytest.raises(VolumeError, match="positive integer"):
            volume_manager._validate_volume_spec(volume_spec, {})
    
    def test_validate_negative_size_fails(self, volume_manager):
        """Test validation rejects negative size."""
        volume_spec = VolumeSpec(name="test", size=-10, volume_type="classic")
        with pytest.raises(VolumeError, match="positive integer"):
            volume_manager._validate_volume_spec(volume_spec, {})
    
    def test_validate_bootable_without_image_id_fails(self, volume_manager):
        """Test validation rejects bootable volume without image_id."""
        volume_spec = VolumeSpec(
            name="boot-vol",
            size=50,
            volume_type="classic",
            bootable=True
        )
        with pytest.raises(VolumeError, match="requires image_id"):
            volume_manager._validate_volume_spec(volume_spec, {})
    
    def test_validate_bootable_with_image_id_succeeds(self, volume_manager):
        """Test validation accepts bootable volume with image_id."""
        volume_spec = VolumeSpec(
            name="boot-vol",
            size=50,
            volume_type="classic",
            bootable=True,
            image_id="img-123"
        )
        # Should not raise
        volume_manager._validate_volume_spec(volume_spec, {})
    
    def test_validate_attach_to_nonexistent_instance_fails(self, volume_manager):
        """Test validation rejects attach_to referencing non-existent instance."""
        volume_spec = VolumeSpec(
            name="test",
            size=100,
            volume_type="classic",
            attach_to="nonexistent-instance"
        )
        with pytest.raises(VolumeError, match="non-existent instance"):
            volume_manager._validate_volume_spec(volume_spec, {})
    
    def test_validate_attach_to_inactive_instance_fails(self, volume_manager):
        """Test validation rejects attach_to instance not in ACTIVE status."""
        volume_spec = VolumeSpec(
            name="test",
            size=100,
            volume_type="classic",
            attach_to="test-instance"
        )
        
        inactive_instance = Mock()
        inactive_instance.status = "BUILD"
        instances = {"test-instance": inactive_instance}
        
        with pytest.raises(VolumeError, match="expected ACTIVE"):
            volume_manager._validate_volume_spec(volume_spec, instances)
    
    def test_validate_attach_to_active_instance_succeeds(
        self, volume_manager, mock_instance
    ):
        """Test validation accepts attach_to instance in ACTIVE status."""
        volume_spec = VolumeSpec(
            name="test",
            size=100,
            volume_type="classic",
            attach_to="test-instance"
        )
        
        instances = {"test-instance": mock_instance}
        # Should not raise
        volume_manager._validate_volume_spec(volume_spec, instances)


class TestCreateVolume:
    """Tests for _create_volume method."""
    
    def test_create_volume_success(self, volume_manager, mock_connection, mock_volume):
        """Test successful volume creation."""
        volume_spec = VolumeSpec(name="test", size=100, volume_type="classic")
        
        mock_connection.block_storage.create_volume.return_value = mock_volume
        
        result = volume_manager._create_volume(volume_spec)
        
        assert result == mock_volume
        mock_connection.block_storage.create_volume.assert_called_once_with(
            name="test",
            size=100,
            volume_type="classic"
        )
    
    def test_create_volume_sdk_exception(self, volume_manager, mock_connection):
        """Test volume creation with SDK exception."""
        volume_spec = VolumeSpec(name="test", size=100, volume_type="classic")
        
        mock_connection.block_storage.create_volume.side_effect = SDKException("API error")
        
        with pytest.raises(VolumeError, match="Failed to create volume"):
            volume_manager._create_volume(volume_spec)
    
    def test_create_volume_unexpected_exception(self, volume_manager, mock_connection):
        """Test volume creation with unexpected exception."""
        volume_spec = VolumeSpec(name="test", size=100, volume_type="classic")
        
        mock_connection.block_storage.create_volume.side_effect = Exception("Unexpected")
        
        with pytest.raises(VolumeError, match="Unexpected error"):
            volume_manager._create_volume(volume_spec)


class TestWaitForVolumeAvailable:
    """Tests for _wait_for_volume_available method."""
    
    def test_wait_volume_already_available(
        self, volume_manager, mock_connection, mock_volume
    ):
        """Test waiting for volume that is already available."""
        mock_connection.block_storage.get_volume.return_value = mock_volume
        
        result = volume_manager._wait_for_volume_available("vol-123")
        
        assert result == mock_volume
        assert result.status == "available"
    
    def test_wait_volume_becomes_available(self, volume_manager, mock_connection):
        """Test waiting for volume that becomes available."""
        creating_volume = Mock()
        creating_volume.id = "vol-123"
        creating_volume.status = "creating"
        
        available_volume = Mock()
        available_volume.id = "vol-123"
        available_volume.status = "available"
        
        mock_connection.block_storage.get_volume.side_effect = [
            creating_volume,
            creating_volume,
            available_volume
        ]
        
        result = volume_manager._wait_for_volume_available("vol-123")
        
        assert result.status == "available"
    
    def test_wait_volume_error_state(self, volume_manager, mock_connection):
        """Test waiting for volume that enters error state."""
        error_volume = Mock()
        error_volume.id = "vol-123"
        error_volume.status = "error"
        
        mock_connection.block_storage.get_volume.return_value = error_volume
        
        with pytest.raises(VolumeError, match="entered error state"):
            volume_manager._wait_for_volume_available("vol-123")
    
    def test_wait_volume_timeout(self, volume_manager, mock_connection):
        """Test waiting for volume with timeout."""
        creating_volume = Mock()
        creating_volume.id = "vol-123"
        creating_volume.status = "creating"
        
        mock_connection.block_storage.get_volume.return_value = creating_volume
        
        # Set very short timeout for testing
        volume_manager.VOLUME_AVAILABLE_TIMEOUT = 0.1
        
        with pytest.raises(VolumeError, match="Timeout waiting"):
            volume_manager._wait_for_volume_available("vol-123")


class TestAttachVolumeToInstance:
    """Tests for _attach_volume_to_instance method."""
    
    def test_attach_volume_success(
        self, volume_manager, mock_connection, mock_volume, mock_instance
    ):
        """Test successful volume attachment."""
        mock_attachment = Mock()
        mock_attachment.id = "attach-123"
        mock_connection.compute.create_volume_attachment.return_value = mock_attachment
        
        # Should not raise
        volume_manager._attach_volume_to_instance(mock_volume, mock_instance)
        
        mock_connection.compute.create_volume_attachment.assert_called_once_with(
            server=mock_instance,
            volume_id=mock_volume.id
        )
    
    def test_attach_volume_sdk_exception(
        self, volume_manager, mock_connection, mock_volume, mock_instance
    ):
        """Test volume attachment with SDK exception."""
        mock_connection.compute.create_volume_attachment.side_effect = SDKException(
            "Attachment failed"
        )
        
        with pytest.raises(VolumeError, match="Failed to attach volume"):
            volume_manager._attach_volume_to_instance(mock_volume, mock_instance)
    
    def test_attach_volume_unexpected_exception(
        self, volume_manager, mock_connection, mock_volume, mock_instance
    ):
        """Test volume attachment with unexpected exception."""
        mock_connection.compute.create_volume_attachment.side_effect = Exception(
            "Unexpected"
        )
        
        with pytest.raises(VolumeError, match="Unexpected error attaching"):
            volume_manager._attach_volume_to_instance(mock_volume, mock_instance)


class TestVerifyVolumeInUse:
    """Tests for _verify_volume_in_use method."""
    
    def test_verify_volume_already_in_use(self, volume_manager, mock_connection):
        """Test verifying volume that is already in-use."""
        in_use_volume = Mock()
        in_use_volume.id = "vol-123"
        in_use_volume.status = "in-use"
        
        mock_connection.block_storage.get_volume.return_value = in_use_volume
        
        result = volume_manager._verify_volume_in_use("vol-123")
        
        assert result.status == "in-use"
    
    def test_verify_volume_becomes_in_use(self, volume_manager, mock_connection):
        """Test verifying volume that becomes in-use."""
        attaching_volume = Mock()
        attaching_volume.id = "vol-123"
        attaching_volume.status = "attaching"
        
        in_use_volume = Mock()
        in_use_volume.id = "vol-123"
        in_use_volume.status = "in-use"
        
        mock_connection.block_storage.get_volume.side_effect = [
            attaching_volume,
            in_use_volume
        ]
        
        result = volume_manager._verify_volume_in_use("vol-123")
        
        assert result.status == "in-use"
    
    def test_verify_volume_error_state(self, volume_manager, mock_connection):
        """Test verifying volume that enters error state."""
        error_volume = Mock()
        error_volume.id = "vol-123"
        error_volume.status = "error"
        
        mock_connection.block_storage.get_volume.return_value = error_volume
        
        with pytest.raises(VolumeError, match="entered error state"):
            volume_manager._verify_volume_in_use("vol-123")


class TestListVolumes:
    """Tests for list_volumes method."""
    
    def test_list_volumes_success(self, volume_manager, mock_connection, mock_volume):
        """Test listing volumes successfully."""
        mock_connection.block_storage.volumes.return_value = [mock_volume]
        
        result = volume_manager.list_volumes()
        
        assert len(result) == 1
        assert result[0] == mock_volume
    
    def test_list_volumes_exception(self, volume_manager, mock_connection):
        """Test listing volumes with exception."""
        mock_connection.block_storage.volumes.side_effect = Exception("API error")
        
        result = volume_manager.list_volumes()
        
        assert result == []


class TestDeleteVolume:
    """Tests for delete_volume method."""
    
    def test_delete_volume_success(self, volume_manager, mock_connection):
        """Test deleting volume successfully."""
        result = volume_manager.delete_volume("vol-123")
        
        assert result is True
        mock_connection.block_storage.delete_volume.assert_called_once_with("vol-123")
    
    def test_delete_volume_exception(self, volume_manager, mock_connection):
        """Test deleting volume with exception."""
        mock_connection.block_storage.delete_volume.side_effect = Exception("API error")
        
        result = volume_manager.delete_volume("vol-123")
        
        assert result is False


class TestDetachVolume:
    """Tests for detach_volume method."""
    
    def test_detach_volume_success(self, volume_manager, mock_connection):
        """Test detaching volume successfully."""
        result = volume_manager.detach_volume("inst-123", "vol-123")
        
        assert result is True
        mock_connection.compute.delete_volume_attachment.assert_called_once_with(
            "vol-123", "inst-123"
        )
    
    def test_detach_volume_exception(self, volume_manager, mock_connection):
        """Test detaching volume with exception."""
        mock_connection.compute.delete_volume_attachment.side_effect = Exception(
            "API error"
        )
        
        result = volume_manager.detach_volume("inst-123", "vol-123")
        
        assert result is False
