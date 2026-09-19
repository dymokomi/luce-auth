#!/usr/bin/env python3
"""Compile and run luce-auth tests."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODES = {f"native{i}": ["--native", "--opt", str(i)] for i in range(4)}
MODES.update({"c": ["--backend=c"], "c-release": ["--backend=c", "--release"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=[*MODES, "all"], default="all")
    parser.add_argument("--base", type=Path, default=Path(os.environ.get("LUCE_BASE_COMPILER", ROOT / "build/toolchain/luce-base")))
    parser.add_argument("--luce", type=Path, default=Path(os.environ.get("LUCE_COMPILER", ROOT / "build/toolchain/luce")))
    args = parser.parse_args()
    environment = dict(os.environ, LUCE_BASE=str(args.base.resolve()))
    environment.setdefault("LUCE_STD", str(ROOT.parent / "luce-base/src/std"))
    environment.setdefault("LUCE_CACHE", str(ROOT / "build/cache"))

    def run(command):
        print("RUN", " ".join(str(a) for a in command), flush=True)
        timeout = 600 if len(command) > 1 and command[1] == "build" else 180
        subprocess.run([str(a) for a in command], cwd=ROOT, env=environment, check=True, timeout=timeout)

    for mode, flags in MODES.items():
        if args.mode not in (mode, "all"):
            continue
        print(f"MODE {mode}", flush=True)
        output = ROOT / "build" / mode
        output.mkdir(parents=True, exist_ok=True)
        run([args.base.resolve(), "build", ROOT / "tests/password.lucb", *flags, "-o", output / "password"])
        run([output / "password", "production"])
        run([args.base.resolve(), "build", ROOT / "tests/password_storage.lucb", *flags, "-o", output / "password-storage"])
        run([args.base.resolve(), "build", ROOT / "tests/check.lucb", *flags, "-o", output / "auth"])
        run([args.base.resolve(), "build", ROOT / "tests/invite_atomic.lucb", *flags, "-o", output / "invite-atomic"])
        run([args.base.resolve(), "build", ROOT / "tests/bootstrap_race.lucb", *flags, "-o", output / "bootstrap-race"])
        run([args.luce.resolve(), "build", ROOT / "tests/facade.luc", *flags, "-o", output / "facade"])
        with tempfile.TemporaryDirectory(prefix="luce-auth-") as tmp:
            run([output / "password-storage", Path(tmp) / "production.db", Path(tmp) / "test-profile.db"])
            run([output / "auth", Path(tmp) / "auth.db", Path(tmp) / "attach.db"])
            run([output / "invite-atomic", Path(tmp) / "invite.db"])
            for attempt in range(8):
                run([output / "bootstrap-race", Path(tmp) / f"race-{attempt}.db"])
            run([output / "facade", Path(tmp) / "facade.db"])
        print(f"PASS {mode}", flush=True)
    print("PASS luce-auth selected compiler modes", flush=True)


if __name__ == "__main__":
    main()
