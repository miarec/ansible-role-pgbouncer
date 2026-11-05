# 2026-10-04-upload-tls-files

Moves the TLS file upload into the role, so a renewed certificate restarts only the service that reads it.

## 🎯 Problem

The ansible-miarec playbooks deploy several services, often on one host, and upload the TLS files of each service with a shared task in `pre_tasks`. Each play then restarts its service from `post_tasks` when a variable registered by that task reports a change. Registered variables survive across plays, so one changed certificate restarts every service deployed later on the same host, including services that never read the file. The playbooks also depend on a variable name internal to the shared task file.

---

## 👀 What changes for users

Before, the role expected the TLS files to exist on the host. After, setting `pgbouncer_client_tls_*_src` and `pgbouncer_server_tls_*_src` makes the role copy the files from the Ansible control machine, set root ownership with mode 0644 for certificates and 0640 for private keys readable by the PGBouncer group, and restarts PGBouncer when a file changed. Leaving the variables empty, the default, keeps the previous behavior.

The role sets permissions only on the files it uploads. A missing parent directory is created as `0755 root:root`, regardless of the host's umask. An existing directory is left alone, so pointing a `*_file` variable at a shared directory such as `/etc/ssl/private` doesn't lock other services out of it.

With TLS enabled, the role also checks that the PGBouncer service user can read every TLS file in use, uploaded or not, before it writes the configuration file. A key that PGBouncer can't open used to surface only at the next restart. Now the play fails first, naming the user and the path, and leaves the running configuration untouched.

---

## 💥 Impact

* **Who is affected**: deployments that set the new `*_src` variables, starting with ansible-miarec.
* **Who is not affected**: existing deployments. The defaults are empty, so no new task runs and no restart is added.
* **Conditions**: `pgbouncer_client_tls` or `pgbouncer_server_tls` enabled and at least one `*_src` variable set. The readability check runs whenever TLS is enabled, so a deployment whose service user can't read its TLS files fails earlier than before, at the check instead of at the restart.

---

## 🔧 Implementation notes

* The upload runs right after the package install, which creates the service account, and before the configuration file is written. `tasks/tls_upload.yml` creates only missing directories and sets ownership and mode only on the files it copies. `tasks/tls_verify.yml` then runs `test -r` on every TLS file in use as `pgbouncer_user`, through `runuser`, which applies the user's supplementary groups the way systemd does.
* The client and server sides usually share one CA file. The shared file is then listed twice, and the second copy is a no-op.
* The TLS Molecule scenarios generate the certificates on the control machine, in a play on `localhost`, and let the role upload them, so a passing test proves the upload. Nothing in prepare writes to `/etc/pgbouncer/tls`, so the test also covers the role creating that directory. The CA private key never reaches the target, and verify asserts that. In `tls-full`, prepare uploads the PostgreSQL server certificate and the CA certificate into `/etc/postgresql/tls` itself. `tls_src_dir` is defined once, in each scenario's `molecule.yml`, as an inventory group var, so it reaches the `localhost` play too.
* The tests assert that the uploaded key is `root:<service group>` 0640 and the certificates 0644 in a `0755 root` directory, that PGBouncer runs as its service user, and that this user can read the key through `runuser`. The service user is `postgres` on Debian and `pgbouncer` on RedHat, so the tests read it from the running process.
* `.yamllint` mirrors the rules that `.ansible-lint` skips and sets the values ansible-lint requires, so `yamllint .` passes and ansible-lint doesn't warn about an incompatible config. `.gitattributes` keeps line endings LF on every checkout.
* The scenarios load the role by path, like ansible-role-miarecweb does, so they also work when the repository is checked out under another directory name.
* These are the same changes as miarec/ansible-role-miarec#13, ported to this role.
