# ansible-role-pgbouncer
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

