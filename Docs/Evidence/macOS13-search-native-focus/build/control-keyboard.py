"""Only explicit CLI commands/read-only polling for the one supervised native input case."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

out = Path(__file__).resolve().parent.parent / 'search-native13-keyboard-runtime'
ready = json.loads((out / 'ready.json').read_text())
env = {k: v for k, v in os.environ.items() if not k.startswith('BERN_')}
env.update(BERN_IPC_DIR=ready['ipc_dir'], BERN_APPEARANCE='light')
args = sys.argv[1:]
wait = args == ['wait-search'] or args == ['wait-query']
assert wait or args == ['ui', 'select', '--target', 'main_window.pages', '--option', 'Library'] or args == ['ui', 'inspect']
end = time.monotonic() + 8
while True:
    command = ['ui', 'inspect'] if wait else args
    stem = 'external-' + str(time.monotonic_ns())
    p = subprocess.run([ready['cli'], '--session', ready['session'], *command], env=env,
                       capture_output=True, timeout=max(0.01, min(8, end - time.monotonic())))
    (out / (stem + '.stdout.json')).write_bytes(p.stdout)
    (out / (stem + '.stderr.txt')).write_bytes(p.stderr)
    (out / (stem + '.command.json')).write_text(json.dumps({'arguments': ['--session', ready['session'], *command],
        'returncode': p.returncode, 'root_request': args}, indent=2) + '\n')
    assert p.returncode == 0, stem
    data = json.loads(p.stdout)
    if not wait:
        print(json.dumps({'stem': stem, 'data': data})); break
    def field(target, role):
        found = [r for r in data if r.get('target') == target and r.get('role') == role and r.get('window') == ready['window']]
        assert len(found) <= 1
        if not found:
            return None
        assert found[0]['enabled'] is True
        return found[0]['value']
    search = field('main_window.sidebar_search', 'search')
    page = field('main_window.pages', 'sidebar')
    if args == ['wait-search']:
        assert page in [None, 'Text'] and search in [None, '', '!']
        if page == 'Text' and search == '!':
            print(json.dumps({'stem': stem, 'search': '!', 'page': page})); break
    else:
        assert page in [None, 'Text', 'Library'] and search in [None, '!']
        summary = field('library_page.library_results', 'query')
        expected = 'failed v1 invalid_search: search text cannot start with `!`; search operators are not supported'
        if page == 'Library' and search == '!' and summary == expected:
            print(json.dumps({'stem': stem, 'search': '!', 'page': page, 'query': summary})); break
        assert summary in [None, 'loading v1', expected], summary
    assert time.monotonic() < end, {'search': search, 'page': page}
    time.sleep(0.12)
