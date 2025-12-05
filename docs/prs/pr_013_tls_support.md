## Summary

Add comprehensive TLS/SSL support for PGBouncer, enabling encrypted connections for both client-side (clients to PGBouncer) and server-side (PGBouncer to PostgreSQL backend) communication.

---

## Purpose

TLS encryption is essential for securing database connections in production environments, especially when traffic traverses untrusted networks. This PR addresses the security gap by:
- Allowing encrypted connections from application clients to PGBouncer
- Enabling encrypted connections from PGBouncer to PostgreSQL backends
- Supporting certificate-based validation for both connection directions

---

## Testing

How did you verify it works?

* [x] Added/updated tests
* [x] Ran `ansible-lint`
* Notes:
  - Added two new Molecule test scenarios:
    - `tls-client`: Tests client-side TLS only (clients -> PGBouncer encrypted, PGBouncer -> PostgreSQL plain)
    - `tls-full`: Tests end-to-end TLS (both client and server connections encrypted)
  - Tests verify TLS connection establishment, certificate validation, and rejection of non-TLS connections when required
  - CI workflow updated to run TLS tests across all supported distros (ubuntu2204, ubuntu2404, rockylinux9, rhel9)

---

## Related Issues

N/A

---

## Changes

Brief list of main changes:

* Added 17 new TLS-related variables in `defaults/main.yml`:
  - Client TLS: `pgbouncer_client_tls`, `pgbouncer_client_tls_sslmode`, `pgbouncer_client_tls_ca_file`, `pgbouncer_client_tls_key_file`, `pgbouncer_client_tls_cert_file`, `pgbouncer_client_tls_protocols`, `pgbouncer_client_tls_ciphers`, `pgbouncer_client_tls_dheparams`, `pgbouncer_client_tls_ecdhcurve`
  - Server TLS: `pgbouncer_server_tls`, `pgbouncer_server_tls_sslmode`, `pgbouncer_server_tls_ca_file`, `pgbouncer_server_tls_key_file`, `pgbouncer_server_tls_cert_file`, `pgbouncer_server_tls_protocols`, `pgbouncer_server_tls_ciphers`
* Updated `templates/pgbouncer.ini.j2` to conditionally render TLS configuration sections
* Added comprehensive TLS documentation to README.md with examples and SSL mode reference table
* Added two new Molecule test scenarios (`tls-client`, `tls-full`) with testinfra tests
* Updated CI workflow with two new jobs to test TLS scenarios across all supported distros

---

## Notes for Reviewers

- TLS sections are conditionally rendered in the config only when `pgbouncer_client_tls` or `pgbouncer_server_tls` are enabled (set to `true`)
- Default SSL mode is `prefer` for both client and server connections to match PGBouncer defaults
- Default protocol is `secure` (TLS 1.2+) and default ciphers are `fast` for good security/performance balance
- Certificate files must be provisioned separately before running this role with TLS enabled

---

## Docs

* [x] Updated relevant documentation (README.md includes TLS configuration section with examples)
