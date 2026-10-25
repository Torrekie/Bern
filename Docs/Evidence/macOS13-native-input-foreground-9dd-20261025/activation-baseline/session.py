"""One future session: 240-second active ceiling, finish sentinel and owned cleanup."""
import sys
sys.dont_write_bytecode = True
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import tempfile
import time
from common import APP, GUARD, HERE, RUN, command, kernel_identity, load_lock, original_hashes, runtime_environment, same_identity, sha, write

def watch():
    lock = load_lock()
    original_hashes()
    assert not RUN.exists() and not RUN.is_symlink(), 'One-shot run directory must be absent'
    RUN.mkdir()
    started = time.monotonic()
    deadline = started + 240
    initial = json.loads(command([GUARD, 'inspect', APP], RUN, 'before-launch').stdout)
    assert initial['own'] is None and initial['front'] is not None and initial['front']['kernel_start'] is not None
    write(RUN / 'original-front.json', initial['front'])
    env = runtime_environment(lock)
    ipc = Path(lock['ipc'])
    ipc.mkdir(mode=0o700)
    write(RUN / 'environment.json', {'BERN_IPC_DIR': str(ipc), 'inherited_BERN_variables_removed': True,
          'appearance_and_motion': 'Inherited system defaults; no render, appearance, motion or observer overrides.',
          'deadline_monotonic': deadline, 'active_seconds_ceiling': 240, 'cleanup_separately_bounded': True})
    child = None
    own = None
    cleanup = {'success': False}
    failure = None
    try:
        with (RUN / 'application.log').open('wb') as log:
            child = subprocess.Popen([str(APP / 'Contents/MacOS/Showcase'), '-AppleLanguages', '(en)', '-AppleLocale', 'en_US'], env=env, stdout=log, stderr=log)
        raw = kernel_identity(child.pid)
        assert raw is not None and raw['ppid'] == os.getpid() and raw['executable_path'] == str(APP / 'Contents/MacOS/Showcase')
        own = {'pid': child.pid, 'bundle_id': lock['identifier'], 'executable_path': raw['executable_path'],
               'kernel_start': raw['kernel_start'], 'launch_date': None, 'watcher_pid': os.getpid()}
        write(RUN / 'own.json', own)
        write(RUN / 'spawn-kernel.json', raw)
        startup = min(deadline, time.monotonic() + 18)
        sequence = 0
        while time.monotonic() < startup and child.poll() is None:
            sequence += 1
            remaining = startup - time.monotonic()
            observed = json.loads(command([GUARD, 'inspect', APP], RUN, 'startup-identity-' + str(sequence), timeout=min(5, remaining)).stdout)
            if same_identity(observed['own'], own):
                remaining = startup - time.monotonic()
                assert remaining > 0, 'Startup expired before sessions read'
                result = command([lock['cli'], 'sessions'], RUN, 'sessions-' + str(sequence), env=env, allow=True, timeout=min(8, remaining))
                try:
                    sessions = json.loads(result.stdout)
                    if result.returncode == 0 and len(sessions) == 1:
                        write(RUN / 'ready.json', {'pid': child.pid, 'session': sessions[0]['session_id'], 'ipc': str(ipc),
                              'cli': lock['cli'], 'app': str(APP), 'private_bundle_id': lock['identifier'],
                              'kernel_start': own['kernel_start'], 'deadline_monotonic': deadline,
                              'deadline_epoch_approximate': time.time() + deadline - time.monotonic(),
                              'ipc_ready_only': True, 'native_window_or_field_ready_unverified': True,
                              'foreground_not_yet_requested_by_driver': True})
                        break
                except (ValueError, KeyError, TypeError):
                    pass
            time.sleep(min(0.2, max(0, startup - time.monotonic())))
        assert (RUN / 'ready.json').exists(), 'Startup did not become ready'
        while time.monotonic() < deadline and not (RUN / 'finish').exists() and child.poll() is None:
            time.sleep(0.2)
        cleanup['end_reason'] = 'finish' if (RUN / 'finish').exists() else ('child_exit' if child.poll() is not None else 'deadline')
    except BaseException as error:
        failure = repr(error)
    finally:
        cleanup.update({'child_started': child is not None, 'failure': failure, 'active_elapsed_seconds': time.monotonic() - started})
        errors = []
        try:
            if own is not None:
                result = command([GUARD, 'cleanup', APP, RUN / 'original-front.json', RUN / 'own.json'], RUN, 'cleanup-guard', allow=True)
                cleanup['guard_returncode'] = result.returncode
                cleanup['guard'] = json.loads(result.stdout)
            post = json.loads(command([GUARD, 'inspect', APP], RUN, 'post-cleanup-identity').stdout)
            cleanup['post'] = post
            # Only for a direct child that never registered as an NSRunningApplication.
            raw = kernel_identity(child.pid) if child is not None and child.poll() is None else None
            if raw is not None and post['own'] is None and own is not None:
                assert raw['ppid'] == os.getpid() and raw['executable_path'] == own['executable_path'] and raw['kernel_start'] == own['kernel_start']
                assert post['front'] is None or post['front']['pid'] != child.pid, 'Never stop a foreground child without Guard restoration'
                child.terminate()
                try: child.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    again = kernel_identity(child.pid)
                    assert again == raw, 'Direct child kernel identity changed'
                    os.kill(child.pid, signal.SIGKILL)
                    child.wait(timeout=1)
                cleanup['unregistered_direct_child_fallback'] = {'kernel_identity': raw, 'not_foreground': True, 'exit': child.returncode}
            if child is not None:
                try: cleanup['child_exit'] = child.wait(timeout=4)
                except subprocess.TimeoutExpired: cleanup['child_exit'] = 'still-running-preserved'
            assert post['own'] is None and (child is None or child.poll() is not None), 'Owned instance remains; preserve runtime artifacts'
            identifier = lock['identifier']
            prefs = Path.home() / 'Library/Preferences' / (identifier + '.plist')
            if prefs.exists():
                assert not prefs.is_symlink()
                result = command(['/usr/bin/defaults', 'delete', identifier], RUN, 'private-preferences-delete', timeout=60, allow=True)
                if prefs.exists():
                    assert plistlib.loads(prefs.read_bytes()) == {}, 'Private preferences not empty after bounded delete'
                    prefs.unlink()
                assert result.returncode == 0 or not prefs.exists()
            state_paths = [Path.home() / 'Library/Saved Application State' / (identifier + '.savedState'), Path(tempfile.gettempdir()) / (identifier + '.savedState')]
            for state in state_paths:
                if state.exists():
                    assert not state.is_symlink() and state.is_dir()
                    shutil.rmtree(state)
            assert not ipc.is_symlink() and not any(p.is_symlink() for p in ipc.rglob('*'))
            cleanup['ipc_members_before_removal'] = [str(p.relative_to(ipc)) for p in ipc.rglob('*')]
            shutil.rmtree(ipc)
            cleanup.update({'private_preferences_absent': not prefs.exists(), 'saved_states_absent': all(not p.exists() for p in state_paths), 'ipc_absent': not ipc.exists()})
            # Future single-use runtime products are no longer needed after all guard/control subprocesses ended.
            removed = {'private_app_logical_bytes': sum(p.stat().st_size for p in APP.rglob('*') if p.is_file()), 'guard_logical_bytes': GUARD.stat().st_size,
                       'private_gui_sha256': sha(APP / 'Contents/MacOS/Showcase'), 'guard_sha256': sha(GUARD)}
            assert removed['private_gui_sha256'] == lock['private_gui_sha256'] and removed['guard_sha256'] == lock['guard_sha256']
            shutil.rmtree(APP)
            GUARD.unlink()
            cleanup['owned_runtime_products_removed'] = removed
            cleanup['success'] = cleanup.get('guard_returncode', 0) == 0 and failure is None
        except BaseException as error:
            errors.append(repr(error))
        try: cleanup['original_four_binaries'] = original_hashes()
        except BaseException as error: errors.append(repr(error))
        cleanup['cleanup_errors'] = errors
        cleanup['success'] = cleanup['success'] and not errors
        write(RUN / 'cleanup.json', cleanup)
    return 0 if cleanup['success'] else 1

if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] == 'watch', 'Usage: python3 session.py watch (root only; launches private App)'
    raise SystemExit(watch())
