"""Unit tests for SecurityGroupManager."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from openstack.exceptions import SDKException

from openstack_sdk.security_group_manager import SecurityGroupManager, SecurityGroupError
from config.models import SecurityGroupSpec, SecurityGroupRule


@pytest.fixture
def mock_connection():
    """Create a mock OpenStack connection."""
    conn = Mock()
    conn.network = Mock()
    return conn


@pytest.fixture
def security_group_manager(mock_connection):
    """Create a SecurityGroupManager instance with mock connection."""
    return SecurityGroupManager(mock_connection)


@pytest.fixture
def valid_sg_spec():
    """Create a valid security group specification."""
    return SecurityGroupSpec(
        name="test-sg",
        description="Test security group",
        rules=[
            SecurityGroupRule(
                direction="ingress",
                protocol="tcp",
                port_range_min=22,
                port_range_max=22,
                remote_ip_prefix="0.0.0.0/0",
                ethertype="IPv4"
            ),
            SecurityGroupRule(
                direction="ingress",
                protocol="tcp",
                port_range_min=80,
                port_range_max=80,
                remote_ip_prefix="0.0.0.0/0",
                ethertype="IPv4"
            )
        ]
    )


class TestSecurityGroupCreation:
    """Tests for security group creation."""
    
    def test_create_security_groups_success(self, security_group_manager, mock_connection, valid_sg_spec):
        """Test successful security group creation."""
        # Mock security group
        mock_sg = Mock()
        mock_sg.id = "sg-123"
        mock_sg.name = "test-sg"
        
        # Mock rule
        mock_rule = Mock()
        mock_rule.id = "rule-123"
        
        mock_connection.network.create_security_group.return_value = mock_sg
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        # Create security groups
        result = security_group_manager.create_security_groups([valid_sg_spec])
        
        # Verify
        assert len(result) == 1
        assert result[0].id == "sg-123"
        mock_connection.network.create_security_group.assert_called_once()
        assert mock_connection.network.create_security_group_rule.call_count == 2
    
    def test_create_security_groups_empty_list(self, security_group_manager):
        """Test creating security groups with empty list."""
        result = security_group_manager.create_security_groups([])
        assert result == []
    
    def test_create_security_groups_duplicate_names(self, security_group_manager):
        """Test that duplicate security group names are rejected."""
        sg_spec1 = SecurityGroupSpec(name="duplicate-sg", description="First", rules=[])
        sg_spec2 = SecurityGroupSpec(name="duplicate-sg", description="Second", rules=[])
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_groups([sg_spec1, sg_spec2])
        
        assert "Duplicate security group names" in str(exc_info.value)
        assert "duplicate-sg" in str(exc_info.value)
    
    def test_create_security_groups_sdk_exception(self, security_group_manager, mock_connection, valid_sg_spec):
        """Test handling of SDK exceptions during creation."""
        mock_connection.network.create_security_group.side_effect = SDKException("API error")
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_groups([valid_sg_spec])
        
        assert "Failed to create security group" in str(exc_info.value)
    
    def test_create_security_group_tracks_names(self, security_group_manager, mock_connection):
        """Test that created security group names are tracked."""
        sg_spec1 = SecurityGroupSpec(name="sg-1", description="First", rules=[])
        sg_spec2 = SecurityGroupSpec(name="sg-2", description="Second", rules=[])
        
        mock_sg1 = Mock(id="sg-1-id", name="sg-1")
        mock_sg2 = Mock(id="sg-2-id", name="sg-2")
        
        mock_connection.network.create_security_group.side_effect = [mock_sg1, mock_sg2]
        
        security_group_manager.create_security_groups([sg_spec1, sg_spec2])
        
        assert "sg-1" in security_group_manager._created_sg_names
        assert "sg-2" in security_group_manager._created_sg_names


class TestSecurityGroupRuleCreation:
    """Tests for security group rule creation."""
    
    def test_create_rule_tcp_with_ports(self, security_group_manager, mock_connection):
        """Test creating TCP rule with port range."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=80,
            port_range_max=80,
            remote_ip_prefix="0.0.0.0/0",
            ethertype="IPv4"
        )
        
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        result = security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert result.id == "rule-123"
        mock_connection.network.create_security_group_rule.assert_called_once()
        call_args = mock_connection.network.create_security_group_rule.call_args[1]
        assert call_args['direction'] == 'ingress'
        assert call_args['protocol'] == 'tcp'
        assert call_args['port_range_min'] == 80
        assert call_args['port_range_max'] == 80
    
    def test_create_rule_any_protocol(self, security_group_manager, mock_connection):
        """Test creating rule with 'any' protocol."""
        rule = SecurityGroupRule(
            direction="egress",
            protocol="any",
            remote_ip_prefix="0.0.0.0/0",
            ethertype="IPv4"
        )
        
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        security_group_manager.create_security_group_rule("sg-123", rule)
        
        call_args = mock_connection.network.create_security_group_rule.call_args[1]
        assert call_args['protocol'] is None  # 'any' becomes None in OpenStack
    
    def test_create_rule_icmp(self, security_group_manager, mock_connection):
        """Test creating ICMP rule."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="icmp",
            remote_ip_prefix="10.0.0.0/8",
            ethertype="IPv4"
        )
        
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        result = security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert result.id == "rule-123"
        call_args = mock_connection.network.create_security_group_rule.call_args[1]
        assert call_args['protocol'] == 'icmp'
    
    def test_create_rule_ipv6(self, security_group_manager, mock_connection):
        """Test creating IPv6 rule."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=443,
            port_range_max=443,
            remote_ip_prefix="::/0",
            ethertype="IPv6"
        )
        
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        security_group_manager.create_security_group_rule("sg-123", rule)
        
        call_args = mock_connection.network.create_security_group_rule.call_args[1]
        assert call_args['ethertype'] == 'IPv6'
        assert call_args['remote_ip_prefix'] == '::/0'


class TestRuleValidation:
    """Tests for security group rule validation."""
    
    def test_validate_invalid_direction(self, security_group_manager):
        """Test that invalid direction is rejected."""
        rule = SecurityGroupRule(
            direction="invalid",
            protocol="tcp",
            remote_ip_prefix="0.0.0.0/0"
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid direction" in str(exc_info.value)
    
    def test_validate_invalid_protocol(self, security_group_manager):
        """Test that invalid protocol is rejected."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="invalid",
            remote_ip_prefix="0.0.0.0/0"
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid protocol" in str(exc_info.value)
    
    def test_validate_invalid_ethertype(self, security_group_manager):
        """Test that invalid ethertype is rejected."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            remote_ip_prefix="0.0.0.0/0",
            ethertype="IPv5"  # Invalid
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid ethertype" in str(exc_info.value)
    
    def test_validate_port_range_min_greater_than_max(self, security_group_manager):
        """Test that port_range_min > port_range_max is rejected."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=100,
            port_range_max=50,  # Less than min
            remote_ip_prefix="0.0.0.0/0"
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid port range" in str(exc_info.value)
        assert "must be less than or equal to" in str(exc_info.value)
    
    def test_validate_port_range_min_out_of_bounds(self, security_group_manager):
        """Test that port numbers outside valid range are rejected."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=-1,  # Invalid
            port_range_max=80,
            remote_ip_prefix="0.0.0.0/0"
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid port_range_min" in str(exc_info.value)
    
    def test_validate_port_range_max_out_of_bounds(self, security_group_manager):
        """Test that port numbers outside valid range are rejected."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=80,
            port_range_max=70000,  # Invalid
            remote_ip_prefix="0.0.0.0/0"
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid port_range_max" in str(exc_info.value)
    
    def test_validate_invalid_cidr(self, security_group_manager):
        """Test that invalid CIDR notation is rejected."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            remote_ip_prefix="invalid-cidr"
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid CIDR notation" in str(exc_info.value)
    
    def test_validate_cidr_without_prefix(self, security_group_manager):
        """Test that CIDR without prefix is rejected."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            remote_ip_prefix="192.168.1.0"  # Missing /24
        )
        
        with pytest.raises(SecurityGroupError) as exc_info:
            security_group_manager.create_security_group_rule("sg-123", rule)
        
        assert "Invalid CIDR notation" in str(exc_info.value)
    
    def test_validate_valid_cidr_ranges(self, security_group_manager, mock_connection):
        """Test that various valid CIDR ranges are accepted."""
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        valid_cidrs = [
            "0.0.0.0/0",
            "192.168.1.0/24",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "::/0",
            "2001:db8::/32"
        ]
        
        for cidr in valid_cidrs:
            rule = SecurityGroupRule(
                direction="ingress",
                protocol="tcp",
                remote_ip_prefix=cidr,
                ethertype="IPv6" if ":" in cidr else "IPv4"
            )
            # Should not raise exception
            security_group_manager.create_security_group_rule("sg-123", rule)


class TestSecurityGroupQueries:
    """Tests for security group query operations."""
    
    def test_get_security_group_by_name_found(self, security_group_manager, mock_connection):
        """Test getting security group by name when it exists."""
        mock_sg = Mock(id="sg-123", name="test-sg")
        mock_connection.network.security_groups.return_value = [mock_sg]
        
        result = security_group_manager.get_security_group_by_name("test-sg")
        
        assert result is not None
        assert result.id == "sg-123"
        mock_connection.network.security_groups.assert_called_once_with(name="test-sg")
    
    def test_get_security_group_by_name_not_found(self, security_group_manager, mock_connection):
        """Test getting security group by name when it doesn't exist."""
        mock_connection.network.security_groups.return_value = []
        
        result = security_group_manager.get_security_group_by_name("nonexistent")
        
        assert result is None
    
    def test_get_security_group_by_name_exception(self, security_group_manager, mock_connection):
        """Test handling exception when getting security group by name."""
        mock_connection.network.security_groups.side_effect = Exception("API error")
        
        result = security_group_manager.get_security_group_by_name("test-sg")
        
        assert result is None
    
    def test_list_security_groups(self, security_group_manager, mock_connection):
        """Test listing all security groups."""
        mock_sgs = [Mock(id="sg-1"), Mock(id="sg-2")]
        mock_connection.network.security_groups.return_value = mock_sgs
        
        result = security_group_manager.list_security_groups()
        
        assert len(result) == 2
        assert result[0].id == "sg-1"
        assert result[1].id == "sg-2"
    
    def test_list_security_groups_exception(self, security_group_manager, mock_connection):
        """Test handling exception when listing security groups."""
        mock_connection.network.security_groups.side_effect = Exception("API error")
        
        result = security_group_manager.list_security_groups()
        
        assert result == []


class TestSecurityGroupDeletion:
    """Tests for security group deletion."""
    
    def test_delete_security_group_success(self, security_group_manager, mock_connection):
        """Test successful security group deletion."""
        result = security_group_manager.delete_security_group("sg-123")
        
        assert result is True
        mock_connection.network.delete_security_group.assert_called_once_with("sg-123")
    
    def test_delete_security_group_exception(self, security_group_manager, mock_connection):
        """Test handling exception during security group deletion."""
        mock_connection.network.delete_security_group.side_effect = Exception("API error")
        
        result = security_group_manager.delete_security_group("sg-123")
        
        assert result is False


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_port_range_equal_min_max(self, security_group_manager, mock_connection):
        """Test that equal port_range_min and port_range_max is valid."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=80,
            port_range_max=80,
            remote_ip_prefix="0.0.0.0/0"
        )
        
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        # Should not raise exception
        security_group_manager.create_security_group_rule("sg-123", rule)
    
    def test_port_range_boundary_values(self, security_group_manager, mock_connection):
        """Test boundary port values (0 and 65535)."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=0,
            port_range_max=65535,
            remote_ip_prefix="0.0.0.0/0"
        )
        
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        # Should not raise exception
        security_group_manager.create_security_group_rule("sg-123", rule)
    
    def test_rule_without_ports(self, security_group_manager, mock_connection):
        """Test creating rule without port specifications."""
        rule = SecurityGroupRule(
            direction="ingress",
            protocol="icmp",
            remote_ip_prefix="0.0.0.0/0"
        )
        
        mock_rule = Mock(id="rule-123")
        mock_connection.network.create_security_group_rule.return_value = mock_rule
        
        security_group_manager.create_security_group_rule("sg-123", rule)
        
        call_args = mock_connection.network.create_security_group_rule.call_args[1]
        assert 'port_range_min' not in call_args or call_args.get('port_range_min') is None
        assert 'port_range_max' not in call_args or call_args.get('port_range_max') is None
    
    def test_security_group_with_no_rules(self, security_group_manager, mock_connection):
        """Test creating security group with no rules."""
        sg_spec = SecurityGroupSpec(
            name="empty-sg",
            description="Security group with no rules",
            rules=[]
        )
        
        mock_sg = Mock(id="sg-123", name="empty-sg")
        mock_connection.network.create_security_group.return_value = mock_sg
        
        result = security_group_manager.create_security_groups([sg_spec])
        
        assert len(result) == 1
        assert result[0].id == "sg-123"
        # No rules should be created
        mock_connection.network.create_security_group_rule.assert_not_called()
