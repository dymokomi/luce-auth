#!/usr/bin/env python3
"""Explicit macOS leak gate for native auth, including Prism persistence."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import heap_process

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', type=Path, default=ROOT / 'build/toolchain/luce-base')
args = parser.parse_args()
if sys.platform != 'darwin':
    raise SystemExit('macOS leaks tool required; use Linux sanitizer gate otherwise')
env = dict(os.environ)
env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
out = ROOT / 'build/heap'
out.mkdir(parents=True, exist_ok=True)
subprocess.run([os.environ.get('CC', 'cc'), str(ROOT / 'tests/heap_canary.c'),
                '-o', str(out / 'canary-c')], check=True, timeout=60)
subprocess.run([str(args.base.resolve()), 'build', str(ROOT / 'tests/heap_canary.lucb'),
                '--native', '-o', str(out / 'canary-native')], env=env, cwd=ROOT, check=True, timeout=600)
for name in ['canary-c', 'canary-native']:
    print(f'HEAP INSTRUMENTATION CANARY {name}', flush=True)
    result = heap_process.run(['/usr/bin/leaks', '--quiet', '--noContent', '--atExit', '--', out / name], env=env)
    print(result.stdout, end='', flush=True)
    print(result.stderr, end='', file=sys.stderr, flush=True)
    result.check_returncode()
    assert 'PASS ' in result.stdout, 'heap instrumentation canary did not complete'
    assert '0 leaks for 0 total leaked bytes' in result.stdout, result.stdout
for name in ['check', 'invite_atomic', 'bootstrap_race', 'password_storage']:
    binary = out / name
    subprocess.run([str(args.base.resolve()), 'build', str(ROOT / 'tests' / f'{name}.lucb'),
                    '--native', '-o', str(binary)], env=env, cwd=ROOT, check=True, timeout=600)
    # leaks reports its own exit status, not the fixture's. Verify ordinary child
    # status separately, with a fresh store for each run, and require completion
    # evidence from the instrumented fixture as well as the zero-leak report.
    for instrumented in (False, True):
        with tempfile.TemporaryDirectory(prefix='auth-heap-') as temporary:
            paths = [str(Path(temporary) / 'auth.db')]
            if name == 'check': paths.append(str(Path(temporary) / 'attach.db'))
            if name == 'password_storage': paths.append(str(Path(temporary) / 'test-profile.db'))
            prefix = ['/usr/bin/leaks', '--quiet', '--noContent', '--atExit', '--'] if instrumented else []
            print(f'HEAP FIXTURE {name} instrumented={instrumented}', flush=True)
            result = heap_process.run([*prefix, str(binary), *paths], env=env)
            print(result.stdout, end='', flush=True)
            print(result.stderr, end='', file=sys.stderr, flush=True)
            result.check_returncode()
            assert 'PASS ' in result.stdout, 'auth fixture did not report completion'
            if instrumented:
                assert '0 leaks for 0 total leaked bytes' in result.stdout, result.stdout
print('PASS native auth and persistence heap cleanup')
