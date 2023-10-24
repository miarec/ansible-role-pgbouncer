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


### TLS
pgbouncer can support TLS in two modes,   server-side and client-side

#### server-side
pgbouncer communicates to a database,  pgbouncer can supply TLS certificates if mutal TLS authentication is required by the database.

 - `pgbouncer_server_tls` If true, pgbouncer will be configured to use TLS to connect to a backend
 - `pgbouncer_server_tls_ca_file` Root certificate file to validate PostgreSQL server certificates.
 - `pgbouncer_server_tls_key_file` Private key for PgBouncer to authenticate against PostgreSQL server
 - `pgbouncer_server_tls_cert_file` Certificate for private key. PostgreSQL server can validate it.

#### client-side
pgbouncer recieves inbound traffic from a client requesting access to a database, pgbouncer will negotiate TLS using its certificates.

 - `pgbouncer_client_tls` If true, pgbouncer will be configured to use TLS for inbound connections from clients
 - `pgbouncer_client_tls_ca_file` Root certificate file to validate client certificates, if presented
 - `pgbouncer_client_tls_key_file` Private key for PgBouncer to accept client connections.
 - `pgbouncer_client_tls_cert_file` Certificate for private key. Clients can validate it.





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

