variable "auth_url" {
  description = "The authentication URL for OVH OpenStack API (reads from TF_VAR_auth_url or set via env OS_AUTH_URL)"
  type        = string
  sensitive   = false
  default     = null
}

# variable "username" {
#   description = "The username for OVH OpenStack authentication"
#   type        = string
#   sensitive   = true
# }

# variable "password" {
#   description = "The password for OVH OpenStack authentication"
#   type        = string
#   sensitive   = true
# }

variable "tenant_name" {
  description = "The tenant/project name for OVH OpenStack (reads from TF_VAR_tenant_name or set via env OS_PROJECT_NAME)"
  type        = string
  sensitive   = false
  default     = null
}

variable "application_credential_id" {
  description = "The application credential ID for OVH OpenStack authentication (reads from TF_VAR_application_credential_id or set via env OS_APPLICATION_CREDENTIAL_ID)"
  type        = string
  sensitive   = true
  default     = null
}

variable "application_credential_secret" {
  description = "The application credential secret for OVH OpenStack authentication (reads from TF_VAR_application_credential_secret or set via env OS_APPLICATION_CREDENTIAL_SECRET)"
  type        = string
  sensitive   = true
  default     = null
}

variable "region" {
  description = "The OVH OpenStack region (reads from TF_VAR_region or set via env OS_REGION_NAME)"
  type        = string
  sensitive   = false
  default     = null
}

# Instance Configuration Variables
variable "instance_count" {
  description = "Number of compute instances to create"
  type        = number
  default     = 1
}

variable "instance_flavor" {
  description = "The flavor/size for compute instances (e.g., scale-1, s1-8)"
  type        = string
  default     = "scale-1"
}

variable "instance_image" {
  description = "The image name or ID for compute instances (e.g., Debian 12 LVM OPCP, Debian 11)"
  type        = string
  default     = "Debian 12 LVM OPCP"
}

variable "key_name" {
  description = "The SSH key name for instance access"
  type        = string
  default     = "opcp-openstack-automation-ssh-key"
}

# Network Configuration Variables
variable "network_name" {
  description = "Name of the private network to create"
  type        = string
  default     = "private-network"
}

variable "subnet_cidr" {
  description = "CIDR notation for the subnet (e.g., 192.168.1.0/24)"
  type        = string
  default     = "192.168.1.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_cidr, 0))
    error_message = "The subnet_cidr value must be a valid CIDR notation (e.g., 192.168.1.0/24)."
  }
}

variable "dns_nameservers" {
  description = "List of DNS nameservers for the subnet"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "enable_dhcp" {
  description = "Enable DHCP for the subnet"
  type        = bool
  default     = true
}

# Volume Configuration Variables
variable "volume_size" {
  description = "Size of volumes in GB"
  type        = number
  default     = 100

  validation {
    condition     = var.volume_size > 0
    error_message = "Volume size must be a positive integer."
  }
}

variable "volume_count" {
  description = "Number of volumes to create"
  type        = number
  default     = 0

  validation {
    condition     = var.volume_count >= 0
    error_message = "Volume count must be a non-negative integer."
  }
}

variable "volume_type" {
  description = "Type of volume (e.g., classic, high-speed)"
  type        = string
  default     = "classic"
}

variable "volume_bootable" {
  description = "Whether volumes should be bootable"
  type        = bool
  default     = false
}

variable "volume_image_id" {
  description = "Image ID for bootable volumes (required if volume_bootable is true)"
  type        = string
  default     = null
}

# Security Group Configuration Variables
variable "security_group_name" {
  description = "Name of the security group to create"
  type        = string
  default     = "default-security-group"
}

variable "security_group_description" {
  description = "Description of the security group"
  type        = string
  default     = "Default security group for instances"
}

variable "allow_ssh_from" {
  description = "CIDR range allowed to access SSH (port 22)"
  type        = string
  default     = "0.0.0.0/0"

  validation {
    condition     = can(cidrhost(var.allow_ssh_from, 0))
    error_message = "The allow_ssh_from value must be a valid CIDR notation (e.g., 192.168.1.0/24 or 0.0.0.0/0)."
  }
}

variable "allow_http" {
  description = "Allow HTTP traffic (port 80)"
  type        = bool
  default     = true
}

variable "allow_https" {
  description = "Allow HTTPS traffic (port 443)"
  type        = bool
  default     = true
}

# Instance Metadata and User Data Variables
variable "instance_metadata" {
  description = "Metadata tags to apply to instances (key-value pairs)"
  type        = map(string)
  default     = {}
}

variable "instance_user_data" {
  description = "User data script to inject into instances (cloud-init script)"
  type        = string
  default     = null
}

# Student Configuration Variables
variable "student_id" {
  description = "Student identifier — used as the Linux username created on instances via cloud-init"
  type        = string
}

variable "student_password" {
  description = "Password for the student user created on instances. MUST be set before running terraform apply (export TF_VAR_student_password)"
  type        = string
  sensitive   = true
}
