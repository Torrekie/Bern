"""Bounded reads and Inputs-page setup for the one running owned session."""
import sys
sys.dont_write_bytecode = True
import json
import re
import time
from common import APP, GUARD, RUN, command, load_lock, runtime_environment, same_identity, write

def main():
    assert len(sys.argv) == 3, 'Usage: control.py UNIQUE-LABEL state|inspect|inputs'
    label, operation = sys.argv[1:]
    assert re.fullmatch(r'[a-z0-9-]+', label)
    choices = {'state': ['state'], 'inspect': ['ui', 'inspect'],
               'inputs': ['ui', 'select', '--target', 'main_window.pages', '--option', 'Inputs']}
    assert operation in choices
    lock = load_lock()
    ready = json.loads((RUN / 'ready.json').read_text())
    own = json.loads((RUN / 'own.json').read_text())
    assert not (RUN / 'finish').exists() and not (RUN / 'cleanup.json').exists()
    assert time.monotonic() < ready['deadline_monotonic']
    output = RUN / 'cli'
    output.mkdir(exist_ok=True)
    assert not any(output.glob(label + '.*')), 'Action label must be fresh'
    identity = json.loads(command([GUARD, 'inspect', APP], output, label + '-identity', timeout=5).stdout)
    assert same_identity(identity['own'], own) and own['pid'] == ready['pid']
    assert ready['ipc'] == lock['ipc']
    timeout = min(8, ready['deadline_monotonic'] - time.monotonic())
    assert timeout > 0
    result = command([ready['cli'], '--session', ready['session'], *choices[operation]], output, label,
                     timeout=timeout, env=runtime_environment(lock))
    if result.stdout.strip():
        value = json.loads(result.stdout)
        write(output / (label + '.payload.json'), value)
        if operation == 'state':
            print(json.dumps({'revision': value.get('revision'), 'activations': value.get('values', {}).get('activations'), 'last_action': value.get('values', {}).get('last_action')}))
        elif operation == 'inspect':
            print(json.dumps([v for v in value if v.get('target') in ['main_window.pages', 'inputs_page.name']], ensure_ascii=False))
    else:
        print('Inputs setup acknowledged; native navigation/focus/edit/submit acceptance is not asserted.')

if __name__ == '__main__':
    main()
