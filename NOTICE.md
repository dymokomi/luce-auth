# Provenance

Original Luce auth implementation, Copyright 2026 Dy Mokomi, MIT OR Apache-2.0.

Passwords are hashed with Argon2id from `luce-crypto`. Users, invitations and
session tokens are stored as Prism documents via `luce-prism`. No C/C++/Rust
identity engine is included or linked.

Argon2id costs in the first slice (`32 KiB / 1 pass / 1 lane`) are test-only.
Raise them before any real deployment.
