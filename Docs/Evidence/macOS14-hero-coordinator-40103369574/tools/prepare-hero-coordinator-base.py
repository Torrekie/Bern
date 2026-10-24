from pathlib import Path
import json,hashlib,shutil
R=Path.cwd();B=R/'outputs/Bern/.github/scripts/hero-route-probe';D=R/'outputs/Bern/.github/scripts/hero-coordinator-probe';D.mkdir(exist_ok=False)
p=json.loads((B/'source-provenance.json').read_text())
names=['Dependencies.swift','ProductImage.swift','ProductImage.exact.swift','ProductStyle.swift','ProductStyle.exact.swift','ProductHero.exact.swift']
for n in names:
 b=(B/n).read_bytes();assert hashlib.sha256(b).hexdigest()==p['files'][n]['sha256'];shutil.copy2(B/n,D/n)
(D/'assets').mkdir();shutil.copy2(B/'assets/source-named-pq.png',D/'assets/source-named-pq.png')
assert hashlib.sha256((D/'ProductHero.exact.swift').read_bytes()).hexdigest()=='8e1e90a00ff2f386a38ed8c4977af27a505571051560d50406e9e54b69ed186c'
print('Prepared exact core slices and one actual named asset; driver pending')
