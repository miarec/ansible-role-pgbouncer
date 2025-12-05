import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_directories(host):
    dirs = [
        "/etc/pgbouncer",
        "/var/log/pgbouncer",
        "/var/run/pgbouncer"
    ]
    for dir in dirs:
        d = host.file(dir)
        assert d.is_directory
        assert d.exists


def test_files(host):
    files = [
        "/etc/pgbouncer/pgbouncer.ini",
        "/etc/pgbouncer/userlist.txt",
        "/etc/pgbouncer/pgbouncer_hba.conf",
        "/var/log/pgbouncer/pgbouncer.log",
        "/var/run/pgbouncer/pgbouncer.pid"
    ]
    for file in files:
        f = host.file(file)
        assert f.exists
        assert f.is_file


def test_service(host):
    s = host.service("pgbouncer")
    assert s.is_enabled
    assert s.is_running


def test_socket(host):
    sockets = [
        "tcp://0.0.0.0:6432"
    ]
    for socket in sockets:
        s = host.socket(socket)
        assert s.is_listening


def test_postgresql_service(host):
    """Verify PostgreSQL is running."""
    s = host.service("postgresql")
    assert s.is_enabled
    assert s.is_running


def test_postgresql_direct_connectivity(host):
    """Test direct connection to PostgreSQL (bypassing PGBouncer)."""
    # Connect directly to PostgreSQL (port 5432) to verify it's properly configured
    cmd = host.run(
        "PGPASSWORD=testpassword psql -h 127.0.0.1 -p 5432 -U testuser "
        "-d testdb -c 'SELECT 1 AS result;' -t -A"
    )
    assert cmd.rc == 0, f"Direct PostgreSQL connection failed: {cmd.stderr}"
    assert cmd.stdout.strip() == "1", f"Unexpected result: {cmd.stdout}"


def test_pgbouncer_postgresql_connectivity(host):
    """Test that PGBouncer can connect to PostgreSQL and execute a query."""
    # Connect through PGBouncer (port 6432) to the test database
    # and execute SELECT 1 to verify the connection works
    cmd = host.run(
        "PGPASSWORD=testpassword psql -h 127.0.0.1 -p 6432 -U testuser "
        "-d testdb -c 'SELECT 1 AS result;' -t -A"
    )
    assert cmd.rc == 0, f"PGBouncer connection failed: {cmd.stderr}"
    assert cmd.stdout.strip() == "1", f"Unexpected result: {cmd.stdout}"