# Terraform Deployment Solution

This directory contains the Terraform-based deployment solution for OVH OpenStack infrastructure.

## Overview

The Terraform solution provides Infrastructure as Code (IaC) capabilities for deploying and managing OVH OpenStack resources. It uses declarative configuration to define the desired state of infrastructure.

## installation Ubuntu

sudo snap install terraform --classic

## Requirements

- Terraform >= 1.5.0
- terraform-provider-openstack >= 1.51.0
- Valid OVH OpenStack credentials

## Structure

```
terraform/
├── main.tf           # Main Terraform configuration
├── variables.tf      # Input variable definitions
├── outputs.tf        # Output value definitions
├── versions.tf       # Provider version constraints
├── terraform.tfvars  # Variable values (not committed to git)
└── modules/          # Reusable Terraform modules
```

## Usage

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Plan Deployment

```bash
terraform plan -var-file="terraform.tfvars"
```

### Apply Deployment

```bash
terraform apply -var-file="terraform.tfvars"
```

### Destroy Infrastructure

```bash
terraform destroy -var-file="terraform.tfvars"
```

## Configuration

Create a `terraform.tfvars` file with your credentials:

```



```

**Important:** Add `terraform.tfvars` to `.gitignore` to avoid committing credentials.

## Features

- Declarative infrastructure definition
- State management with terraform.tfstate
- Dependency resolution and parallel resource creation
- Idempotent operations
- Plan preview before applying changes

## Coming Soon

Full Terraform implementation will be added in subsequent tasks.
