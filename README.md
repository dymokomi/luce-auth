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
python3 tests/run.py --base ../luce-base/build/luce-base --luce ../luce/build/luce
```
