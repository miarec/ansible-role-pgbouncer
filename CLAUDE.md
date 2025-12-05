This file provides guidance to coding agent when working with code in this repository.

## Project Overview

Ansible role for installing and configuring PGBouncer, a PostgreSQL connection pooler. Supports Ubuntu (22.04, 24.04), RHEL 9, and Rocky Linux 9.

## Commands

### Linting
```bash
uv run ansible-lint
```

### Running Tests
```bash
# Run default test scenario (uses Docker)
uv run molecule test

# Run specific test scenario
uv run molecule test -s tls-client
uv run molecule test -s tls-full

# Test against specific distro
MOLECULE_DISTRO=ubuntu2404 uv run molecule test
MOLECULE_DISTRO=rockylinux9 uv run molecule test

# Available distros: ubuntu2204, ubuntu2404, rockylinux9, rhel9
```

### Test Scenarios
- `default` - Basic PGBouncer installation without TLS
- `tls-client` - TLS enabled for client connections only (clients -> PGBouncer)
- `tls-full` - TLS enabled for both client and server connections (clients -> PGBouncer -> PostgreSQL)

### Molecule Commands
```bash
uv run molecule converge              # Create and provision instance
uv run molecule converge -s tls-full  # Run specific scenario
uv run molecule verify                # Run testinfra tests only
uv run molecule destroy               # Tear down instance
uv run molecule login                 # SSH into test container
```

## Architecture

Standard Ansible role structure:
- `defaults/main.yml` - All configurable variables with defaults
- `tasks/main.yml` - Entry point, imports OS-specific vars and task files
- `tasks/dependencies.yml` - Package installation (APT/YUM repos)
- `tasks/pgbouncer.yml` - Main configuration tasks
- `vars/Debian.yml`, `vars/RedHat.yml` - OS-family specific variables
- `templates/pgbouncer.ini.j2` - Main config template with parameter documentation
- `molecule/*/tests/test_*.py` - Testinfra verification tests for each scenario

## Key Variables

The role exposes many `pgbouncer_*` variables in `defaults/main.yml`. Main ones:
- `pgbouncer_users` - List of users (name/pass) for userlist.txt
- `pgbouncer_databases` - Database connection definitions
- `pgbouncer_pool_mode` - transaction (default), session, or statement
- `pgbouncer_max_client_conn`, `pgbouncer_default_pool_size` - Connection limits

## Linting Configuration

`.ansible-lint` skips: fqcn, yaml line-length/empty-lines/trailing-spaces/truthy, jinja spacing, name template
