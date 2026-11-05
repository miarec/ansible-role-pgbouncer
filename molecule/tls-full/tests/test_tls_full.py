import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

PGBOUNCER_TLS_DIR = "/etc/pgbouncer/tls"
POSTGRESQL_TLS_DIR = "/etc/postgresql/tls"


def pgbouncer_user(host):
    """Return the user PGBouncer runs as: postgres on Debian, pgbouncer on RedHat."""
    users = {p.user for p in host.process.filter(comm="pgbouncer")}
    assert users, "No pgbouncer process is running"
    assert "root" not in users, "A pgbouncer process runs as root"
    assert len(users) == 1, f"pgbouncer runs as more than one user: {users}"
    return users.pop()


def test_pgbouncer_service_running(host):
    """Verify PGBouncer service is enabled and running."""
    s = host.service("pgbouncer")
    assert s.is_enabled
    assert s.is_running


def test_postgresql_service_running(host):
    """Verify PostgreSQL service is enabled and running."""
    s = host.service("postgresql")
    assert s.is_enabled
    assert s.is_running


def test_pgbouncer_port_listening(host):
    """Verify PGBouncer is listening on port 6432."""
    s = host.socket("tcp://0.0.0.0:6432")
    assert s.is_listening


def test_postgresql_ssl_enabled(host):
    """Verify PostgreSQL has SSL enabled."""
    # Check via SHOW ssl command
    cmd = host.run("sudo -u postgres psql -c 'SHOW ssl;' -t -A")
    assert cmd.rc == 0, f"Failed to check SSL: {cmd.stderr}"
    assert "on" in cmd.stdout


def test_pgbouncer_client_tls_config(host):
    """Verify PGBouncer client TLS configuration is present."""
    conf = host.file("/etc/pgbouncer/pgbouncer.ini")
    assert conf.exists
    assert conf.contains("client_tls_sslmode = require")
    assert conf.contains("client_tls_key_file = /etc/pgbouncer/tls/server.key")
    assert conf.contains("client_tls_cert_file = /etc/pgbouncer/tls/server.crt")


def test_pgbouncer_server_tls_config(host):
    """Verify PGBouncer server TLS configuration is present."""
    conf = host.file("/etc/pgbouncer/pgbouncer.ini")
    assert conf.exists
    assert conf.contains("server_tls_sslmode = verify-full")
    assert conf.contains(f"server_tls_ca_file = {PGBOUNCER_TLS_DIR}/postgresql-ca.crt")


def test_tls_certificates_exist(host):
    """Verify the TLS files were uploaded, by the role and by prepare."""
    files = [
        # Uploaded by the role
        *(f"{PGBOUNCER_TLS_DIR}/{name}"
          for name in ("ca.crt", "server.crt", "server.key", "postgresql-ca.crt")),
        # Uploaded by prepare
        *(f"{POSTGRESQL_TLS_DIR}/{name}" for name in ("ca.crt", "server.crt", "server.key")),
    ]
    for path in files:
        f = host.file(path)
        assert f.exists, f"Certificate file {path} does not exist"
        assert f.is_file, f"Not a file: {path}"


def test_ca_key_not_on_host(host):
    """The CA private keys stay on the control machine."""
    for name in ("ca.key", "postgresql-ca.key"):
        assert not host.file(f"{PGBOUNCER_TLS_DIR}/{name}").exists
    assert not host.file(f"{POSTGRESQL_TLS_DIR}/ca.key").exists


def test_each_side_has_its_own_ca(host):
    """The role uploaded two distinct CA files, one per side."""
    client_ca = host.file(f"{PGBOUNCER_TLS_DIR}/ca.crt")
    server_ca = host.file(f"{PGBOUNCER_TLS_DIR}/postgresql-ca.crt")
    assert client_ca.sha256sum != server_ca.sha256sum, "Both sides use the same CA"
    assert server_ca.sha256sum == host.file(f"{POSTGRESQL_TLS_DIR}/ca.crt").sha256sum, \
        "The backend CA does not match the CA PostgreSQL was configured with"


def test_tls_file_permissions(host):
    """The role uploads the private key readable by the service group only."""
    group = host.user(pgbouncer_user(host)).group
    key = host.file(f"{PGBOUNCER_TLS_DIR}/server.key")
    assert key.user == "root", "server.key is not owned by root"
    assert key.group == group, f"server.key is not group {group}"
    assert key.mode == 0o640, "server.key is not 0640"
    for name in ("ca.crt", "server.crt", "postgresql-ca.crt"):
        cert = host.file(f"{PGBOUNCER_TLS_DIR}/{name}")
        assert cert.user == "root", f"{name} is not owned by root"
        assert cert.mode == 0o644, f"{name} is not 0644"
    # The role created the directory, so it has the fixed mode, not the umask.
    tls_dir = host.file(PGBOUNCER_TLS_DIR)
    assert tls_dir.user == "root", "TLS directory is not owned by root"
    assert tls_dir.mode == 0o755, "TLS directory is not 0755"


def test_service_user_can_read_tls_key(host):
    """The service user reads the private key through its group."""
    user = pgbouncer_user(host)
    result = host.run(f"runuser -u {user} -- cat {PGBOUNCER_TLS_DIR}/server.key")
    assert result.rc == 0, f"{user} cannot read server.key: {result.stderr}"


def test_pgbouncer_tls_connection_with_sslmode_require(host):
    """Verify PGBouncer accepts TLS connections with sslmode=require."""
    cmd = host.run(
        'PGPASSWORD=testpassword psql '
        '"host=127.0.0.1 port=6432 user=testuser dbname=testdb sslmode=require" '
        "-c 'SELECT 1;'"
    )
    assert cmd.rc == 0, f"Expected rc=0, got rc={cmd.rc}, stderr={cmd.stderr}"


def test_pgbouncer_tls_connection_with_verify_ca(host):
    """Verify PGBouncer accepts TLS connections with CA verification."""
    cmd = host.run(
        'PGPASSWORD=testpassword psql '
        '"host=127.0.0.1 port=6432 user=testuser dbname=testdb '
        'sslmode=verify-ca sslrootcert=/etc/pgbouncer/tls/ca.crt" '
        "-c 'SELECT 1;'"
    )
    assert cmd.rc == 0, f"Expected rc=0, got rc={cmd.rc}, stderr={cmd.stderr}"


def test_pgbouncer_connection_without_tls_fails(host):
    """Verify PGBouncer rejects non-TLS connections when TLS is required."""
    cmd = host.run(
        'PGPASSWORD=testpassword psql '
        '"host=127.0.0.1 port=6432 user=testuser dbname=testdb sslmode=disable" '
        "-c 'SELECT 1;'"
    )
    # Connection should fail when TLS is required
    assert cmd.rc != 0, "Connection without TLS should be rejected"


def test_postgresql_direct_tls_connection(host):
    """Verify PostgreSQL presents a certificate that chains to the backend CA.

    hostaddr connects to the loopback address while host names the certificate
    subject to verify. libpq before PostgreSQL 16 doesn't match IP addresses in
    certificate SANs, so host=127.0.0.1 alone fails on RedHat 9.
    """
    cmd = host.run(
        'PGPASSWORD=testpassword psql '
        '"hostaddr=127.0.0.1 host=localhost port=5432 user=testuser dbname=testdb '
        f'sslmode=verify-full sslrootcert={PGBOUNCER_TLS_DIR}/postgresql-ca.crt" '
        "-c 'SELECT 1;'"
    )
    assert cmd.rc == 0, f"Expected rc=0, got rc={cmd.rc}, stderr={cmd.stderr}"


def test_postgresql_rejects_client_side_ca(host):
    """The client-facing CA does not validate PostgreSQL, so the CAs are not interchangeable."""
    cmd = host.run(
        'PGPASSWORD=testpassword psql '
        '"host=127.0.0.1 port=5432 user=testuser dbname=testdb '
        f'sslmode=verify-ca sslrootcert={PGBOUNCER_TLS_DIR}/ca.crt" '
        "-c 'SELECT 1;'"
    )
    assert cmd.rc != 0, "PostgreSQL certificate was accepted with the client-facing CA"


def test_full_tls_chain_query(host):
    """Verify full TLS chain works: client -> PGBouncer (TLS) -> PostgreSQL (TLS)."""
    # Execute a query through PGBouncer with TLS and verify it works
    cmd = host.run(
        'PGPASSWORD=testpassword psql '
        '"host=127.0.0.1 port=6432 user=testuser dbname=testdb '
        'sslmode=verify-ca sslrootcert=/etc/pgbouncer/tls/ca.crt" '
        "-c 'SELECT current_database();' -t -A"
    )
    assert cmd.rc == 0, f"Expected rc=0, got rc={cmd.rc}, stderr={cmd.stderr}"
    assert "testdb" in cmd.stdout, f"Expected 'testdb' in output, got: {cmd.stdout}"
