## Summary

Migrate from pip/virtualenv-based testing to `uv` for simpler dependency management, and add end-to-end PostgreSQL connectivity tests to molecule.

---

## Purpose

- Simplify test dependency management using `uv` instead of maintaining a pinned `test-requirements.txt`
- Modernize CI/CD pipeline with streamlined GitHub Actions workflow
- Add proper end-to-end testing that verifies PGBouncer can actually connect to PostgreSQL
- Clean up deprecated Ansible syntax warnings
- Drop support for EOL operating systems (Ubuntu 20.04, CentOS 7, Rocky Linux 8, RHEL 7/8)

---

## Testing

How did you verify it works?

* [x] Added/updated tests
* [x] Ran `uv run ansible-lint`
* Notes: Added end-to-end PostgreSQL connectivity tests that verify both direct PostgreSQL connection and connection through PGBouncer

---

## Related Issues

N/A

---

## Changes

Brief list of main changes:

* **Migrated to `uv`** - Added `pyproject.toml` and `uv.lock`, removed `test-requirements.txt`
* **Updated CI workflow** - GitHub Actions now uses `astral-sh/setup-uv@v4` and `ubuntu-22.04` runner
* **Added end-to-end tests** - New `prepare.yml` sets up PostgreSQL, tests verify actual connectivity
* **Fixed deprecated syntax** - Changed `ansible_os_family` → `ansible_facts['os_family']` throughout
* **Fixed file mode warnings** - Changed octal mode values to strings (e.g., `0755` → `"0755"`)
* **Fixed test file typo** - Renamed `test_defatuls.py` → `test_defaults.py`
* **Dropped EOL distros** - Removed Ubuntu 20.04, CentOS 7, Rocky Linux 8, RHEL 7, RHEL 8
* **Updated documentation** - Added `CLAUDE.md` and expanded README with testing section

---

## Notes for Reviewers

- The `uv.lock` file pins all dependencies for reproducible builds
- Molecule tests now install a real PostgreSQL instance and verify connectivity
- Tests verify both direct PostgreSQL connection (port 5432) and PGBouncer proxy (port 6432)
- CI tests against Ubuntu 22.04, Ubuntu 24.04, Rocky Linux 9, and RHEL 9

---

## Docs

* [x] Updated relevant documentation
