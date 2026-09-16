# Provenance

Original Luce Base LID1 invite encoding and Argon2id + XChaCha20-Poly1305 vault
wrapping, Copyright 2026 Dy Mokomi, MIT OR Apache-2.0. No foreign identity,
KDF or AEAD engine is included or linked.

Record layout is the frozen v1 LID1 header in `luce-pkg-server/docs/CONTRACTS.md`.
Argon2id is RFC 9106 via `luce-crypto`; XChaCha20-Poly1305 is the libsodium
construction over RFC 8439 ChaCha20/Poly1305, also via `luce-crypto`.

Test vault costs (8192 KiB, 1 pass, 1 lane) are not the uncalibrated production
starting point (65536 KiB, 3 passes, 1 lane) and are not calibrated for
real credentials.

Build/test/bootstrap scaffolding follows the MIT OR Apache-2.0 `luce-crypto`
patterns by the same author.
