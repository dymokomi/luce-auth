# luce-auth

## Post-quantum account key proofs

The `account_identity` export generates an owning random32-byte seed, derives a
1952-byte ML-DSA-65 public key, and creates/verifies randomized3309-byte possession
proofs. Store the seed only in an encrypted private vault; never send it to a
registry. Caller-owned seed bytes remain the caller's responsibility to wipe;
temporary expanded private keys are wiped internally. Output buffers are exact
size and unchanged on failure.

The signed message is ASCII `luce-auth/account-possession/v1` followed by NUL,
one-byte origin length, exact origin bytes, one-byte account-name length, account
bytes, and a32-byte challenge. Origins are1..255 printable non-space ASCII bytes;
this layer does not parse or normalize URLs. Account names follow auth syntax.
Registry configuration must supply the canonical expected origin, not accept an
arbitrary claimant-selected one. The proof demonstrates key possession for this
context, not account ownership by itself.

`Authority.key_challenge(session, origin)` authenticates a live session and stores
one random32-byte outstanding challenge per account, replacing any older one.
`Authority.enroll_key(session, origin, public_key, proof)` checks the live session,
stored origin, five-minute challenge lifetime and possession proof. First-key
publication and challenge consumption commit atomically, with a same-session-field
write to conflict with concurrent revocation. Concurrent enrollment contenders
write the same key/consumption fields, so only one can commit. A bound account
cannot issue a new challenge or replace its key through these APIs. Failed proofs
do not consume challenges or publish staged writes. A one-second bounded writer
wait is used for commit/bake. Storage failures after commit can still leave a
published result; inspect state before retrying.

`Authority.signing_key(session)` authorizes the session and reads that account's
key from the same snapshot. It returns an owning optional Value: none only for an
authenticated account without a key; session, storage and malformed-key failures
are errors. The stored key must be a rank-one uint8 array of exactly1952 bytes.
Release a returned reference. Reads neither consume challenges nor mutate state.
A concurrent revocation may occur after the read's snapshot, as with ordinary
session verification. This is own-account reconciliation, not a public key
directory or a release trust-distribution policy.

Authenticated rotation/recovery, issuance rate limits and
durable challenge handling across severe clock rollback remain unfinished.
Origins must be supplied from trusted registry configuration. The host wall clock
must be trustworthy. Replaying identical proof inputs still verifies at the raw
cryptographic layer; the Authority enforces one-use enrollment. These are not package
release signatures and cannot substitute for release verification. No new
external cryptographic review is claimed.

## Native credential vault

The `credential_vault` export wraps 1–8192 opaque credential bytes using native
Argon2id (64 MiB, three passes, four lanes/workers) and XChaCha20-Poly1305.
`seal(password, plaintext)` returns an owning encrypted `crypto_native.Secret`;
`open(password, wire)` returns an owning plaintext Secret only after successful
authentication. Close each returned owner exactly once; borrowed views must not
outlive it. Derived keys and failed plaintext buffers are wiped. Passwords are
1–1024 bytes. There is no low-cost test profile.

LAV1 wire format: magic4, three LE32 KDF costs, LE32 plaintext length, four zero
reserved bytes, random16-byte salt, random24-byte nonce, ciphertext, tag16. The
entire 64-byte header is AEAD associated data. Argon2 associated data is the fixed
ASCII domain `luce-auth/vault/LAV1`. Unknown versions/costs/flags, lengths outside
bounds and trailing bytes are rejected before hashing. Each seal uses fresh OS
entropy. Vault KDFs have their own four-slot nonblocking process-wide admission
gate, separate from account-password hashing; these limits are not an aggregate
application memory quota.

This is a byte-envelope API, not yet a finished `luc` login.
Terminal password input, origin/account binding,
key recovery/rotation and CLI integration remain required. Encryption alone does
not prevent rollback of an old valid vault. The API does not wipe caller-owned
password/plaintext inputs. No independent LAV1 interoperability oracle or external
security review is claimed; native crypto primitives have their own test suites.
Vault roundtrip, tampering, truncation, randomness and boundary tests run in six
compiler modes, ASan/UBSan, and the macOS heap gate.

### Private vault files (Linux/macOS)

`credential_files.create(path, password, plaintext, published)` encrypts before
writing a private temporary sibling, synchronizes its contents, publishes with
atomic no-replace semantics, then synchronizes the parent directory. Requested
permissions are 0600, filtered by umask. Existing entries (including links and
directories) are never overwritten. Optional `published` is reset on entry and
becomes true after publication: a subsequent directory-sync/close error can mean
the file exists but durability is uncertain. Temporary cleanup is best effort.

`credential_files.open(path, password)` requires an owned private parent and
an owned regular single-link file with mode0600 or0400. It atomically refuses a
final symlink, opens nonblocking to avoid FIFO hangs, reads a bounded ciphertext
and returns only authenticated plaintext in a Secret owner. A final symlink for
the parent directory is also refused. The caller must provide a trusted, stable
parent path and ancestors for the whole operation; this is not containment under
hostile ancestor replacement. POSIX permissions do not prevent access by root or
hostile code running as the same user. Parent creation, encrypted-file rollback
protection, authenticated replacement/rotation and recovery remain caller/CLI work.
No plaintext is written by these functions. File tests cover permissions, reopen,
no-clobber, links/FIFO, malformed ciphertext and authentication failures in all six
compiler modes and sanitizers; the heap gate exercises create/read.

The new native `password_records` export provides a versioned 64-byte `LAP1`
record: magic, little-endian memory/passes/lanes, random 16-byte salt, and 32-byte
Argon2id output. Its default `interactive` profile is 65536 KiB / 3 passes / 4
lanes, using four native workers (RFC 9106's second recommended option).
`create` leaves output unchanged on failure; `verify` wipes temporary derived
bytes and uses constant-time comparison. Passwords are bounded to 1–1024 bytes.
Only exact supported cost profiles are accepted before hashing; unknown versions,
lengths, or costs fail. The separate 32 KiB test profile requires explicit creation
selection and `allow_test=true` verification; default verification rejects it.

Authority now persists `password_record` and uses the interactive profile by
default in both `open` and `attach`. Tests may explicitly pass `test_only=true`;
default login and session verification reject test-profile records. Session
verification checks the user's current record profile in the same snapshot.
Unversioned legacy salt/hash accounts and their sessions fail closed: no implicit
weak fallback or automatic migration. Keep old stores backed up; a deliberate
authenticated migration/reset workflow remains to be built, not deletion of data.
Password creation and verification share a process-wide, nonblocking four-slot
KDF admission gate. Exhaustion returns `password_records.busy` / `auth.busy`
before allocating Argon2 working memory; deferred release covers failures. This
bounds active Argon2 memory to 256 MiB plus overhead, not total process memory.
It does not limit request queues, processes, or per-account attempts. Rate limits
and session lifecycle work are still required before real deployment. Full-cost record creation,
correct/wrong-password verification and malformed-record gates run in all six
compiler modes and ASan/UBSan. See [RFC 9106](https://www.rfc-editor.org/rfc/rfc9106.html).

Users, one-use invitations and session tokens on a [luce-prism](../luce-prism)
store. Passwords are Argon2id via [luce-crypto](../luce-crypto). Dual-licensed
MIT OR Apache-2.0.

```toml
[dependencies]
luce_auth = "../luce-auth"
```

```luce
from auth import Authority

let authority = Authority.open(path, "secret")
authority.bootstrap("alice", "password")
let invite = authority.invite()
authority.accept(invite.text_at(), "bob", "bob-pass")
let token = authority.login("alice", "password")
assert(authority.verify(token.text_at()).text_at() == "alice")
```

- `bootstrap` — first user only.
- `invite` / `accept` — one-use codes; a second accept fails.
- `login` / `verify` / `revoke` — bearer session tokens, exactly 32 lowercase hex characters.
- `Authority.attach(store)` — borrow an open `prism.Store` (same flock).

Default Argon2id costs are `64 MiB / 3 passes / 4 lanes`; only explicit fixture
authorities use `32 KiB / 1 pass / 1 lane`. Experimental; not a reviewed identity
provider. Applications still need bounded request queues and rate limits.

Sessions have an absolute 24-hour lifetime, persisted as `issued_at` and
`expires_at` in the same transaction as the principal. Verification fails at the
expiry second, on invalid/missing timestamps, or when wall time precedes issuance.
The raw bearer is never a Prism path or stored field: session records are keyed by
the lowercase SHA-256 digest of the exact 32-character bearer text. Existing
raw-token-keyed records are deliberately not migrated and fail closed.
Legacy sessions without timestamps fail closed; logging in issues a new session.
No sliding renewal is performed. Expired sessions can still be revoked, but are
not automatically removed: session quotas, garbage collection, password-change
revocation and protection against broader wall-clock rollback remain unfinished.
The host clock must be trustworthy. Malformed tokens are rejected by the library
before storage access, including revoke; HTTP header validation is not the only
boundary.

```sh
python3 tools/bootstrap.py
python3 tests/run.py --mode all
python3 tests/sanitize.py --base build/toolchain/luce-base
```

Bootstrap verifies pinned sibling sources and builds compilers inside this package.
The test runner also accepts explicit `--base` and `--luce` paths. Tests use isolated
temporary databases and cover all four native optimization levels plus C debug/
release, including an actual Luce consumer. Registration regression coverage checks
that a duplicate account does not replace its password or consume the invitation,
and that failed/successful acceptance state survives reopen. Bootstrap checks and
creation share a transaction with a common marker write, because Prism detects
write overlap rather than read predicates. A two-worker bootstrap test is repeated
eight times per mode and requires exactly one first user. Registration commit and
compaction use bounded one-second writer waits. This does not make all auth
operations race-free or eliminate ambiguous outcomes after a committed write.
Sanitizers instrument the native fixtures and runtime, not the high-level Luce
facade. Broader concurrency/fault injection, production KDF settings and
credential custody still require hardening.

On macOS, `python3 tests/heap.py` requires fixture completion and a zero-leak
report, with each ordinary child exit checked separately on a fresh store. Tiny
C and native Luce Base canaries distinguish host instrumentation failures from
authentication/runtime failures. Timeouts remain failures: the runner records
only its own process group's states and bounded macOS stack samples, then cleans
up that test group. Output uses regular files, not pipe EOF: macOS 15's leaks tool
can exit after reporting while its instrumented child remains stopped in
libLeaksAtExit holding output handles. On every tool exit the harness cleans up
remaining group members and preserves the actual tool status; completion/zero-leak
assertions and the separate uninstrumented child check remain mandatory.
`python3 tests/test_heap_process.py` verifies status
preservation and descendant cleanup even after the immediate parent has exited.
The C canary is a test oracle, never part of the library implementation.
