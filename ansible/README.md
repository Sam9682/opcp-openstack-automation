# Ansible Deployment Solution

This directory contains the Ansible-based deployment solution for OVH OpenStack infrastructure.

## Overview

The Ansible solution provides configuration management and deployment capabilities using Ansible playbooks. It offers idempotent operations and declarative resource management.

## Requirements

- Ansible >= 2.14.0
- ansible-collections: openstack.cloud >= 2.0.0
- Python >= 3.8
- openstacksdk >= 1.0.0
- Valid OVH OpenStack credentials

## Structure

```
ansible/
├── playbook.yml          # Main deployment playbook
├── inventory/            # Inventory files
├── group_vars/           # Group variables
├── host_vars/            # Host variables
├── roles/                # Ansible roles
│   └── ovh_deployment/   # Main deployment role
└── requirements.yml      # Ansible collection requirements
```

## Installation

### Install Ansible Collections

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

## Usage

### Deploy Infrastructure

```bash
ansible-playbook ansible/playbook.yml \
  -e auth_url="https://auth.cloud.ovh.net/v3" \
  -e username="your-username" \
  -e password="your-password" \
  -e tenant_name="your-tenant" \
  -e region="GRA7"
```

### Using Variables File

Create a `vars.yml` file:

```yaml
auth_url: "https://auth.cloud.ovh.net/v3"
username: "your-username"
password: "your-password"
tenant_name: "your-tenant"
region: "GRA7"
```

Run with variables file:

```bash
ansible-playbook ansible/playbook.yml -e @vars.yml
```

### Using Ansible Vault for Credentials

Encrypt sensitive variables:

```bash
ansible-vault encrypt_string 'your-password' --name 'password'
```

### Destroy Infrastructure

```bash
ansible-playbook ansible/playbook.yml \
  -e @vars.yml \
  -e state=absent
```

## Features

- Idempotent operations (safe to run multiple times)
- Declarative resource management
- Task dependencies and ordering
- Built-in error handling
- Resource state verification
- Integration with Ansible ecosystem

## Coming Soon

Full Ansible implementation will be added in subsequent tasks.
