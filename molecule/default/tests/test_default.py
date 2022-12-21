import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_bin(host):
    bins = [
        "/usr/local/bin/python3.6",
        "/usr/local/bin/python3.6m",
        "/usr/local/bin/python3.6m-config",
        "/usr/local/bin/pyvenv-3.6"
    ]
    for bin in bins:
        b = host.file(bin)
        assert b.exists
        assert b.is_file

def test_command(host):
    # Run and check specific status codes in one step
    host.run_test("python3.6 --version")

    output = host.check_output("python3.6 --version")
    assert '3.6.10' in output