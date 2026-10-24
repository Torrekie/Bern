from pathlib import Path
import json
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
directory = Path(sys.argv[1]).resolve()
result = Path(sys.argv[2]).resolve()
status = int(sys.argv[3])
assert directory == root/'observer-work'
assert result == root/'direct-last-resize'
files = [p for p in directory.rglob('*') if p.is_file()] if directory.exists() else []
size = sum(p.stat().st_size for p in files)
if directory.exists():
    shutil.rmtree(directory)
expected = str(root/'isolated/Gallery.app/Contents/MacOS/Gallery')
processes = subprocess.check_output(['ps', '-axo', 'pid=,comm=']).decode()
own = [line.strip() for line in processes.splitlines() if line.strip().split(None, 1)[-1] == expected]
(result/'observer-cleanup.json').write_text(json.dumps(dict(observer_exit_status=status,
    owned_scratch=str(directory), removed_files=len(files), removed_logical_bytes=size,
    owned_scratch_exists=directory.exists(), matching_own_app_processes=own,
    scope='Only this observer executable/module cache was removed; no preferences, history or TCC were modified.'), indent=2)+'\n')
