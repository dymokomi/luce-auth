# luce-auth

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

Argon2id costs in this slice are `32 KiB / 1 pass / 1 lane` so tests stay fast.
Raise them before any real deployment. Experimental; not a reviewed identity
provider.

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
