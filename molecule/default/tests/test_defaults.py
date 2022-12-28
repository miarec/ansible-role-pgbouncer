import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_bin(host):
    bins = [
        "/usr/bin/pgbouncer"
    ]
    for bin in bins:
        b = host.file(bin)
        assert b.exists
        assert b.is_file

def test_files(host):
    files = [
        "/etc/pgbouncer/pgbouncer.ini",
        "/etc/logrotate.d/pgbouncer"
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

