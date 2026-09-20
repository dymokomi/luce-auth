"""POSIX vault persistence oracle; only disposable credentials and private paths."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

def check(binary):
    binary = Path(binary).resolve()
    with tempfile.TemporaryDirectory(prefix='vault-files-') as temporary:
        root = Path(temporary)
        target = root / 'identity.vault'
        def run(action, path=target, success=True):
            result = subprocess.run([str(binary), action, str(path)], capture_output=True, timeout=60)
            assert (result.returncode == 0) == success, (result.returncode, result.stderr)
            assert result.returncode >= 0 and b'Sanitizer' not in result.stderr and b'runtime error:' not in result.stderr
            assert b'disposable registry credentials' not in result.stdout + result.stderr
            assert not list(root.glob('.luce-*')), 'temporary vault leaked'
        run('create')
        original = target.read_bytes()
        assert original[:4] == b'LAV1'
        assert target.stat().st_mode & 0o777 == 0o600
        run('read')
        run('wrong', success=False)
        run('create', success=False)
        assert target.read_bytes() == original
        link = root / 'link'
        link.symlink_to(target)
        run('read', link, False)
        run('create', link, False)
        assert link.is_symlink() and target.read_bytes() == original
        hard = root / 'hard'
        os.link(target, hard)
        run('read', hard, False)
        hard.unlink()
        fifo = root / 'fifo'
        os.mkfifo(fifo, 0o600)
        run('read', fifo, False)
        run('create', fifo, False)
        directory = root / 'directory'
        directory.mkdir(mode=0o700)
        alias = root / 'parent-link'
        alias.symlink_to(directory, target_is_directory=True)
        run('create', alias / 'blocked', False)
        assert not (directory / 'blocked').exists()
        run('read', directory, False)
        run('create', directory, False)
        target.chmod(0o644)
        run('read', success=False)
        target.chmod(0o400)
        run('read')
        target.chmod(0o600)
        run('read', root / 'missing', False)
        root.chmod(0o755)
        run('read', success=False)
        run('create', root / 'forbidden', False)
        assert not (root / 'forbidden').exists()
        root.chmod(0o700)
        target.write_bytes(original[:-1])
        run('read', success=False)
        target.write_bytes(original + b'extra')
        run('read', success=False)
        corrupt = bytearray(original)
        corrupt[-1] ^= 1
        target.write_bytes(corrupt)
        run('read', success=False)
        assert target.read_bytes() == corrupt
    print('PASS vault-file permissions, reopen, no-clobber, links/FIFO and failed authentication', flush=True)

if __name__ == '__main__':
    check(sys.argv[1])
