# luce-auth

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
Admission control and session lifecycle work are still required before real
deployment. Full-cost record creation,
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
- `login` / `verify` / `revoke` — bearer session tokens.
- `Authority.attach(store)` — borrow an open `prism.Store` (same flock).

Default Argon2id costs are `64 MiB / 3 passes / 4 lanes`; only explicit fixture
authorities use `32 KiB / 1 pass / 1 lane`. Experimental; not a reviewed identity
provider. Applications still need bounded concurrent-KDF admission and rate limits.

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
