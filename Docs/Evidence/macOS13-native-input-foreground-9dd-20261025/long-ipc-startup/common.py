"""Owned preparation/runtime paths; importing this module sends no UI events."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = ROOT / 'outputs/Bern'
PREP = HERE / 'preparation'
RUN = HERE / 'run'
APP = HERE / 'products/Showcase.app'
GUARD = HERE / 'tools/FocusGuard'
DELIVERY = {
    'outputs/macOS13/Showcase.app/Contents/MacOS/Showcase': 'cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b',
    'outputs/macOS13/bin/showcase': '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170',
    'outputs/macOS13/Gallery.app/Contents/MacOS/Gallery': 'd44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c',
    'outputs/macOS13/bin/gallery': '31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5',
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.writing')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)

def original_hashes():
    result = {p: sha(ROOT / p) for p in DELIVERY}
    assert result == DELIVERY, 'One of the original four delivered binaries changed'
    return result

def command(argv, directory, label, *, timeout=8, env=None, allow=False):
    argv = [str(v) for v in argv]
    record = {'argv': argv, 'timeout_seconds': timeout, 'start_monotonic': time.monotonic()}
    try:
        result = subprocess.run(argv, capture_output=True, timeout=timeout, env=env)
        stdout, stderr = result.stdout, result.stderr
        record['returncode'] = result.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b'', error.stderr or b''
        record['timed_out'] = True
        raise
    finally:
        (directory / (label + '.stdout')).write_bytes(stdout)
        (directory / (label + '.stderr')).write_bytes(stderr)
        record['end_monotonic'] = time.monotonic()
        write(directory / (label + '.command.json'), record)
    if not allow:
        assert result.returncode == 0, (label, result.returncode, stderr.decode(errors='replace')[:500])
    return result

def load_lock():
    lock = json.loads((PREP / 'isolation.json').read_text())
    assert lock['app'] == str(APP) and lock['guard'] == str(GUARD)
    assert lock['identifier'].startswith('dev.bern.native13.inputfg.')
    assert lock['ipc'] == str(RUN / 'ipc')
    assert sha(APP / 'Contents/MacOS/Showcase') == lock['private_gui_sha256']
    assert sha(GUARD) == lock['guard_sha256']
    return lock

def runtime_environment(lock):
    env = {k: v for k, v in os.environ.items() if not k.startswith('BERN_')}
    env['BERN_IPC_DIR'] = lock['ipc']
    return env

def same_identity(left, right):
    return left is not None and all(left.get(k) == right.get(k)
        for k in ['pid', 'bundle_id', 'executable_path', 'kernel_start'])

def kernel_identity(pid):
    # Public proc_bsdinfo layout from the requested SDK14.2 sys/proc_info.h.
    class BSD(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint32) for name in
            ['flags', 'status', 'xstatus', 'pid', 'ppid', 'uid', 'gid', 'ruid', 'rgid', 'svuid', 'svgid', 'reserved']] + [
            ('comm', ctypes.c_char * 16), ('name', ctypes.c_char * 32)] + [
            (name, ctypes.c_uint32) for name in ['nfiles', 'pgid', 'jobc', 'tdev', 'tpgid']] + [
            ('nice', ctypes.c_int32), ('seconds', ctypes.c_uint64), ('micros', ctypes.c_uint64)]
    assert ctypes.sizeof(BSD) == 136
    library = ctypes.CDLL('/usr/lib/libproc.dylib')
    library.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    library.proc_pidinfo.restype = ctypes.c_int
    library.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    library.proc_pidpath.restype = ctypes.c_int
    row = BSD()
    if library.proc_pidinfo(pid, 3, 0, ctypes.byref(row), ctypes.sizeof(row)) != ctypes.sizeof(row):
        return None
    path = ctypes.create_string_buffer(4096)
    if library.proc_pidpath(pid, path, 4096) <= 0:
        return None
    assert row.pid == pid and row.seconds > 0 and row.micros < 1000000
    return {'pid': pid, 'ppid': row.ppid, 'executable_path': str(Path(os.fsdecode(path.value)).resolve()),
            'kernel_start': {'tv_sec': row.seconds, 'tv_usec': row.micros}}
