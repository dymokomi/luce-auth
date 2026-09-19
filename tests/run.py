#!/usr/bin/env python3
"""Compile and run luce-auth tests."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="native0")
    parser.add_argument("--base", type=Path, default=Path(os.environ.get("LUCE_BASE_COMPILER", ROOT.parent / "luce-base/build/luce-base")))
    parser.add_argument("--luce", type=Path, default=Path(os.environ.get("LUCE_COMPILER", ROOT.parent / "luce/build/luce")))
    args = parser.parse_args()
    environment = dict(os.environ, LUCE_BASE=str(args.base.resolve()))
    output = ROOT / "build" / args.mode
    output.mkdir(parents=True, exist_ok=True)

    def run(command):
        subprocess.run([str(a) for a in command], cwd=ROOT, env=environment, check=True, timeout=180)

    flags = ["--native", "--opt", "0"]
    run([args.base.resolve(), "build", ROOT / "tests/check.lucb", *flags, "-o", output / "auth"])
    run([args.luce.resolve(), "build", ROOT / "tests/facade.luc", *flags, "-o", output / "facade"])
    with tempfile.TemporaryDirectory(prefix="luce-auth-") as tmp:
        run([output / "auth"])
        run([output / "facade", Path(tmp) / "facade.db"])
    print("PASS luce-auth")


if __name__ == "__main__":
    main()
