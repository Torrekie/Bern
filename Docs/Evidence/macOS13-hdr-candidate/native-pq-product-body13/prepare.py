from pathlib import Path
import subprocess,hashlib,difflib,json
D=Path(__file__).resolve().parent
REPO=Path('/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern')
commit='9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
path='crates/bern-backend-swiftui/templates/BernRuntime.swift'
full=subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=REPO,text=True)
a=full.index('enum BernImageFit {');b=full.index('// MARK: - Files',a)
exact=full[a:b].rstrip()+'\n';(D/'ProductImage.exact.swift').write_text(exact)
start=exact.index('        var decoded: CGImage?\n');end=exact.index('        guard let image = decoded ??',start)
original=exact[start:end]
patched=exact[:start]+'''        #if compiler(>=6.0)
'''+original+'''        #else
        // Diagnostic SDK14.2 build: the15+ branch above cannot run on13.
        let decoded: CGImage? = nil
        #endif
'''+exact[end:]
imports='''// Exact product image/cache slice, with one documented diagnostic compiler condition.
import AppKit
import SwiftUI
import Combine
import MetalKit
import CoreImage
import ColorSync
import ImageIO

'''
(D/'ProductImage.swift').write_text(imports+patched)
(D/'sdk14-unreachable-gainmap.patch').write_text(''.join(difflib.unified_diff(exact.splitlines(True),patched.splitlines(True),fromfile='9dd99b7/ProductImage.exact.swift',tofile='diagnostic/ProductImage.swift')))
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
(D/'source-provenance.json').write_text(json.dumps({'commit':commit,'repository_source':path,'full_runtime_sha256':sha(full),'exact_slice_sha256':sha(exact),'diagnostic_file_sha256':sha(imports+patched),'slice_first_line':full[:a].count('\n')+1,'slice_final_line':full[:b].count('\n'),'only_product_slice_change':'Compiler condition around macOS15+/iOS18+ gainmap decode API unavailable to localSDK14.2; actual13 unreachable. Compiler<6 uses constantnil to avoid introducing a nevermutated-var warning. The original product exhaustive-switch warning remains recorded and unmodified.','diagnostic_dependencies':'ObservableObject alias,BernColor.fixed stub,BernMotion values,identityBernPictureHero. Hero excluded; actualbody/cache/Legacy display code included.'},indent=2,sort_keys=True)+'\n')
print(commit,len(exact.splitlines()))
