# ansible-role-pgbouncer
![CI](https://github.com/miarec/ansible-role-pgbouncer/actions/workflows/ci.yml/badge.svg?event=push)

Ansible role to install PGBouncer connection pooler.

Postgres server performance degrades when handling a high number of connection due to a 1:1 mapping of connection to Postgres backend processes. PgBouncer is a threaded pooler which can reduce the number of backend processes and the handshaking involved in setting up a new connection.


## Role Variables

### Users

    pgbouncer_users:
      - name: username
        pass: unencrypted_password
      - name: postgres
        host: unencrypted_password

A list of database users allowed to connect to PGBouncer.

This role creates `userlist.txt` file with the specified users. Password is hashed with MD5.


### Databases

    pgbouncer_databases:
      - name: "mydatabase"
        host: db.example.com
        port: 5432

A list of databases, PGBouncer connects to. By default, it connects to all databases (*) on localhost, port 5432:

    pgbouncer_databases:
      - name: "*"
        host: 127.0.0.1
        port: 5432

### Connection settings:

    pgbouncer_listen_addr: "*"
    pgbouncer_listen_port: 6432


### Pool mode:

    pgbouncer_pool_mode: transaction

### Connection limits

    pgbouncer_max_client_conn: 100
    pgbouncer_max_db_connections: 50
    pgbouncer_max_user_connections: 50

    pgbouncer_default_pool_size: 20

For a complete list of available parameters, check `defaults/main.yml` file.

For a description of each parameter, check comments in `templates/pgbouncer.ini.j2` file or the official PGBouncer documentation.


### TLS Configuration

PGBouncer supports TLS encryption in two modes:

- **Client-side TLS**: Encrypt connections from clients to PGBouncer
- **Server-side TLS**: Encrypt connections from PGBouncer to PostgreSQL backend

#### Client-side TLS (clients → PGBouncer)

Enable TLS for incoming client connections:

```yaml
pgbouncer_client_tls: true
pgbouncer_client_tls_sslmode: require    # require, verify-ca, or verify-full
pgbouncer_client_tls_key_file: /etc/pgbouncer/tls/server.key
pgbouncer_client_tls_cert_file: /etc/pgbouncer/tls/server.crt
pgbouncer_client_tls_ca_file: /etc/pgbouncer/tls/ca.crt  # Optional, for client cert validation
```

#### Server-side TLS (PGBouncer → PostgreSQL)

Enable TLS for connections to PostgreSQL backend:

```yaml
pgbouncer_server_tls: true
pgbouncer_server_tls_sslmode: require    # require, verify-ca, or verify-full
pgbouncer_server_tls_ca_file: /etc/pgbouncer/tls/ca.crt  # For server cert validation
# Optional: client certificate for mutual TLS with PostgreSQL
pgbouncer_server_tls_key_file: /etc/pgbouncer/tls/client.key
pgbouncer_server_tls_cert_file: /etc/pgbouncer/tls/client.crt
```

#### Full TLS Example (End-to-End Encryption)

```yaml
- hosts: db
  become: yes
  vars:
    pgbouncer_users:
      - name: appuser
        pass: secretpassword

    pgbouncer_databases:
      - name: myapp
        host: db.example.com
        port: 5432

    # Client TLS (clients connecting to PGBouncer)
    pgbouncer_client_tls: true
    pgbouncer_client_tls_sslmode: require
    pgbouncer_client_tls_key_file: /etc/pgbouncer/tls/server.key
    pgbouncer_client_tls_cert_file: /etc/pgbouncer/tls/server.crt
    pgbouncer_client_tls_ca_file: /etc/pgbouncer/tls/ca.crt

    # Server TLS (PGBouncer connecting to PostgreSQL)
    pgbouncer_server_tls: true
    pgbouncer_server_tls_sslmode: verify-full
    pgbouncer_server_tls_ca_file: /etc/pgbouncer/tls/ca.crt

  roles:
    - ansible-role-pgbouncer
```

#### SSL Modes Reference

| Mode | Description |
|------|-------------|
| `disable` | No TLS, plain TCP only |
| `allow` | Try plain first, then TLS if rejected |
| `prefer` | Try TLS first, fall back to plain (default) |
| `require` | TLS required, no certificate validation |
| `verify-ca` | TLS required, validate server certificate |
| `verify-full` | TLS required, validate certificate and hostname |

For production environments, use `require`, `verify-ca`, or `verify-full`.


## Testing

This role uses [Molecule](https://molecule.readthedocs.io/) with Docker for testing. [uv](https://docs.astral.sh/uv/) is used for dependency management.

### Prerequisites

- Docker
- uv (install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Running Tests

```bash
# Run full test suite
uv run molecule test

# Test against specific distro
MOLECULE_DISTRO=ubuntu2404 uv run molecule test
MOLECULE_DISTRO=rockylinux9 uv run molecule test
```

### Available Distros

| Distribution   | Variable Value  |
|----------------|-----------------|
| Ubuntu 22.04   | `ubuntu2204`    |
| Ubuntu 24.04   | `ubuntu2404`    |
| Rocky Linux 9  | `rockylinux9`   |
| RHEL 9         | `rhel9`         |

### Molecule Commands

```bash
uv run molecule converge    # Create and provision instance
uv run molecule verify      # Run testinfra tests only
uv run molecule destroy     # Tear down instance
uv run molecule login       # SSH into test container
```

### Linting

```bash
uv run ansible-lint
```

## Dependencies

None.

## Example Playbook

    ---
    - hosts:  db
      become: yes
      vars:
        pgbouncer_users:
          - name: username
            pass: unencrypted_password
          - name: postgres
            host: unencrypted_password

        pgbouncer_databases:
          - name: "*"
            host: 127.0.0.1
            port: 5432

        pgbouncer_max_client_conn: 200

      roles:
        - ansible-role-pgbouncer


## Debugging

If pgbouncer fails to start:-

    sudo -u postgres pgbouncer -d /etc/pgbouncer/pgbouncer.ini -vvvv

Testing a connection to a remote database

    psql -h localhost -p 6432 -U username databasename

## Stats

The default 1.7.2 configuration provides peer authentication of the pgbouncer database to show stats. NOTE: this still requires a userlist.txt entry for the postgres user.

    sudo -u postgres psql -p 6432 pgbouncer -c 'show pool;'

    sudo -u postgres psql -p 6432 pgbouncer -c 'show stats;'

## Reloading / restarting

Key config changes such as pool sizing do not require a full restart

    sudo service pgbouncer reload

