#!/usr/bin/env python3
"""Real full-cost KDF contention in six modes and ASan/UBSan."""
import os
import argparse
import sys
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fixture', choices=['admission_stress', 'vault', 'vault_files'], default='admission_stress')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'build/toolchain/luce-base'
out = ROOT / 'build' / ('admission-modes' if args.fixture == 'admission_stress' else args.fixture.replace('_', '-') + '-modes')
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))

def run(command):
    print('RUN', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=ROOT, env=env, check=True, timeout=600)

def fixture(binary):
    run([sys.executable, ROOT / 'tests/vault_files.py', binary] if args.fixture == 'vault_files' else [binary])

source = ROOT / 'tests' / f'{args.fixture}.lucb'
modes = [(f'native{i}', ['--native', '--opt', str(i)]) for i in range(4)]
modes += [('c', ['--backend=c']), ('c-release', ['--backend=c', '--release'])]
for name, flags in modes:
    binary = out / name
    run([base, 'build', source, *flags, '-o', binary])
    fixture(binary)
runtime = ROOT.parent / 'luce-base/runtime'
generated = out / 'sanitize.c'
binary = out / 'sanitize'
run([base, 'build', source, '--emit=c', '-o', generated])
run([os.environ.get('CC', 'cc'), '-std=gnu11', '-O1', '-g', '-w',
     '-fno-strict-aliasing', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
     '-I', runtime, generated, runtime / 'lucb_rt.c', '-pthread', '-lm', '-o', binary])
env['ASAN_OPTIONS'] = 'halt_on_error=1:abort_on_error=1'
env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
fixture(binary)
print(f'PASS {args.fixture}: six compiler modes and ASan/UBSan', flush=True)
