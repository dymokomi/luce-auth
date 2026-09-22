# luce-auth

Accounts for the Luce package registry, written in Luce Base over Prism storage.
MIT OR Apache-2.0.

- **Invitations.** An operator creates single-use invitation codes; redeeming one
  creates an account with a password. Bootstrap publishes exactly one first user
  even under concurrent attempts.
- **Passwords.** Argon2id (64 MiB, three passes) with a per-account salt; only the
  hash is stored. Admission is bounded so a flood of attempts cannot exhaust the
  key-derivation budget.
- **Sessions.** Login issues a 256-bit bearer token. Only its SHA-256 is persisted,
  never the token. Sessions last until revoked.
- **Scoped credentials.** A session mints short-lived credentials bound to one
  repository and one scope (`git:write` for pushes), revocable independently.

Exports: `auth` (the `Authority`) and `password_records`. Consumers:
[luce-pkg-server](https://github.com/dymokomi/luce-pkg-server).

## Test

```sh
python3 tests/run.py --base ../luce-base/build/luce-base --luce ../luce/build/luce
python3 tests/sanitize.py     # generated-C sanitizers, Linux
python3 tests/heap.py         # macOS leak checks
```
