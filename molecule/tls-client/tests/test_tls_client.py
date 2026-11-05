import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

TLS_DIR = "/etc/pgbouncer/tls"


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


def test_pgbouncer_port_listening(host):
    """Verify PGBouncer is listening on port 6432."""
    s = host.socket("tcp://0.0.0.0:6432")
    assert s.is_listening


def test_pgbouncer_tls_config_exists(host):
    """Verify PGBouncer TLS configuration is present."""
    conf = host.file("/etc/pgbouncer/pgbouncer.ini")
    assert conf.exists
    assert conf.contains("client_tls_sslmode = require")
    assert conf.contains(f"client_tls_key_file = {TLS_DIR}/server.key")
    assert conf.contains(f"client_tls_cert_file = {TLS_DIR}/server.crt")


def test_tls_certificates_exist(host):
    """Verify the role uploaded the TLS files."""
    for name in ("ca.crt", "server.crt", "server.key"):
        f = host.file(f"{TLS_DIR}/{name}")
        assert f.exists, f"Certificate file {f.path} does not exist"
        assert f.is_file, f"Not a file: {f.path}"


def test_ca_key_not_on_host(host):
    """The CA private key stays on the control machine."""
    assert not host.file(f"{TLS_DIR}/ca.key").exists


def test_tls_file_permissions(host):
    """The role uploads the private key readable by the service group only."""
    group = host.user(pgbouncer_user(host)).group
    key = host.file(f"{TLS_DIR}/server.key")
    assert key.user == "root", "server.key is not owned by root"
    assert key.group == group, f"server.key is not group {group}"
    assert key.mode == 0o640, "server.key is not 0640"
    for name in ("ca.crt", "server.crt"):
        cert = host.file(f"{TLS_DIR}/{name}")
        assert cert.user == "root", f"{name} is not owned by root"
        assert cert.mode == 0o644, f"{name} is not 0644"
    # The role created the directory, so it has the fixed mode, not the umask.
    tls_dir = host.file(TLS_DIR)
    assert tls_dir.user == "root", "TLS directory is not owned by root"
    assert tls_dir.mode == 0o755, "TLS directory is not 0755"


def test_service_user_can_read_tls_key(host):
    """The service user reads the private key through its group."""
    user = pgbouncer_user(host)
    result = host.run(f"runuser -u {user} -- cat {TLS_DIR}/server.key")
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
        f'sslmode=verify-ca sslrootcert={TLS_DIR}/ca.crt" '
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


def test_postgresql_backend_connection_is_non_tls(host):
    """Verify PGBouncer connects to PostgreSQL without TLS (as expected for this scenario)."""
    # Check that server_tls_sslmode is not set in the config
    conf = host.file("/etc/pgbouncer/pgbouncer.ini")
    assert not conf.contains("server_tls_sslmode"), \
        "Server TLS should not be configured in tls-client scenario"
