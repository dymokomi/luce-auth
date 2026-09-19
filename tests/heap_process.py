"""Bounded POSIX test subprocesses; diagnose and kill only our own process group."""
import os
import signal
import subprocess
import sys


def diagnose(group):
    """No unrelated command lines or environment variables are logged."""
    try:
        result = subprocess.run(['ps', '-axo', 'pid=,ppid=,pgid=,stat=,comm='],
                                capture_output=True, text=True, timeout=5, check=True)
        members = []
        for row in result.stdout.splitlines():
            fields = row.split(None, 4)
            if len(fields) == 5 and int(fields[2]) == group:
                print('TIMED-OUT TEST PROCESS:', row, file=sys.stderr, flush=True)
                members.append(int(fields[0]))
        if sys.platform == 'darwin':
            for pid in members[:4]:
                # Sampling failure must never prevent cleanup of the test group.
                sample = subprocess.run(['/usr/bin/sample', str(pid), '1', '1'],
                                        capture_output=True, text=True, timeout=5)
                print(sample.stdout, file=sys.stderr, flush=True)
                print(sample.stderr, file=sys.stderr, flush=True)
    except (OSError, ValueError, subprocess.SubprocessError) as failure:
        print('Test timeout diagnostics failed:', failure, file=sys.stderr, flush=True)


def run(command, *, env=None, timeout=120, diagnostics=True):
    """Like run(capture_output=True), with descendant cleanup on timeout."""
    command = list(map(str, command))
    with subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                if diagnostics:
                    diagnose(process.pid)
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout, stderr = process.communicate(timeout=5)
            # Preserve captured evidence and remain a failed gate; never retry or
            # treat an instrumentation timeout as proof of zero leaks.
            print(stdout, end='', flush=True)
            print(stderr, end='', file=sys.stderr, flush=True)
            raise subprocess.TimeoutExpired(command, timeout, stdout, stderr) from None
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
