#!/usr/bin/env python3
"""Instrument native auth fixtures and the runtime; not the Luce facade."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / 'build/sanitize'
    output.mkdir(parents=True, exist_ok=True)
    runtime = ROOT.parent / 'luce-base/runtime'
    env = dict(os.environ)
    env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
    env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
    env['ASAN_OPTIONS'] = 'halt_on_error=1:abort_on_error=1'
    env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'

    def run(command):
        print('RUN', ' '.join(str(arg) for arg in command), flush=True)
        subprocess.run([str(arg) for arg in command], cwd=ROOT, env=env,
                       check=True, timeout=600)

    for name in ('check', 'invite_atomic', 'bootstrap_race', 'password'):
        generated = output / f'{name}.c'
        run([args.base.resolve(), 'build', ROOT / 'tests' / f'{name}.lucb',
             '--emit=c', '-o', generated])
        run([os.environ.get('CC', 'cc'), '-std=gnu11', '-O1', '-g', '-w',
             '-fno-strict-aliasing', '-fsanitize=address,undefined',
             '-fno-omit-frame-pointer', '-I', runtime, generated,
             runtime / 'lucb_rt.c', '-pthread', '-lm', '-o', output / name])
    with tempfile.TemporaryDirectory(prefix='luce-auth-sanitize-') as temporary:
        run([output / 'password', 'production'])
        scratch = Path(temporary)
        run([output / 'check', scratch / 'auth.db', scratch / 'attach.db'])
        run([output / 'invite_atomic', scratch / 'invite.db'])
        run([output / 'bootstrap_race', scratch / 'race.db'])
    print('PASS auth native AddressSanitizer + UndefinedBehaviorSanitizer', flush=True)


if __name__ == '__main__':
    main()
