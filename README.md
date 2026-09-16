# luce-auth

Native Luce Base invitation records and password vault wrapping.
MIT OR Apache-2.0. LID1 invites are single-use encodings; vaults wrap identity
material with Argon2id and XChaCha20-Poly1305. Tokens are stored as SHA-256
digests of the secret, never the secret.

Experimental. Not a complete account service, recovery flow or reviewed
credential store. Do not use with real invitations or passwords.

```sh
python3 tools/bootstrap.py
python3 tests/run.py
python3 tests/sanitize.py
```
