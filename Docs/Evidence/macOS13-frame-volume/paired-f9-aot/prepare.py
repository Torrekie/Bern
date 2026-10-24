"""Prepare only: no GUI, generated CLI, focus helper or UI execution."""
import difflib
import hashlib
import json
import plistlib
import shutil
import struct
import subprocess
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent
WORKSPACE = BASE.parent.parent
SOURCE = 'f9e08b1d55bed4b9d880b19934abe48281057bb3'
SOURCE_SCRIPT = WORKSPACE / 'outputs/Bern/.github/scripts/gallery-frame-reference.swift'
ORIGINAL_APP = WORKSPACE / 'outputs/macOS13/Gallery.app'
ORIGINAL_CLI = WORKSPACE / 'outputs/macOS13/bin/gallery'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def command(args, name):
    p = subprocess.run(args, text=True, capture_output=True, check=False)
    (BASE / name).write_text(p.stdout + p.stderr)
    assert p.returncode == 0, (args, p.returncode, p.stderr)
    return p.stdout


def macho(path):
    data = path.read_bytes()
    magic, cpu, subtype, kind, count, command_bytes, flags, reserved = struct.unpack_from('<IiiIIIII', data)
    assert magic == 0xfeedfacf and cpu == 0x100000c and kind == 2
    offset = 32
    sections, build = [], None
    for _ in range(count):
        cmd, size = struct.unpack_from('<II', data, offset)
        assert size >= 8 and offset + size <= 32 + command_bytes <= len(data)
        if cmd == 0x32:
            platform, minimum, sdk, tools = struct.unpack_from('<IIII', data, offset + 8)
            fmt = lambda v: f'{v >> 16}.{(v >> 8) & 255}.{v & 255}'
            build = {'platform': platform, 'minimum': fmt(minimum), 'sdk': fmt(sdk)}
        if cmd == 0x19:
            seg = struct.unpack_from('<II16sQQQQiiII', data, offset)
            assert 72 + seg[-2] * 80 <= size
            for n in range(seg[-2]):
                s = struct.unpack_from('<16s16sQQIIIIIIII', data, offset + 72 + n * 80)
                zero = (s[8] & 255) in (1, 12, 18)
                assert zero or s[4] + s[3] <= len(data)
                sections.append({'segment': s[1].rstrip(b'\0').decode(), 'section': s[0].rstrip(b'\0').decode(),
                                 'size': s[3], 'offset': s[4], 'flags': s[8], 'zero_fill': zero,
                                 'sha256': None if zero else hashlib.sha256(data[s[4]:s[4] + s[3]]).hexdigest()})
        offset += size
    assert offset == 32 + command_bytes
    assert build == {'platform': 1, 'minimum': '13.0.0', 'sdk': '26.2.0'}, build
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'architecture': 'arm64', 'build_version': build, 'sections': sections}


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


baseline = SOURCE_SCRIPT.read_text()
text = baseline


def replace(old, new):
    global text
    assert text.count(old) == 1, old[:100]
    text = text.replace(old, new)


replace('// Heartbeats are CI-only, process-targeted mouseMoved events, not physical mouse acceptance.',
        '// Explicit local13/CI heartbeats are own-active-PID mouseMoved events, not physical mouse acceptance.')
replace('let ciHeartbeat = ProcessInfo.processInfo.environment["GITHUB_ACTIONS"] == "true" && ProcessInfo.processInfo.environment["CI"] == "true"',
        '''let ciHeartbeat = ProcessInfo.processInfo.environment["GITHUB_ACTIONS"] == "true" && ProcessInfo.processInfo.environment["CI"] == "true"
let requestedLocalEvents = ProcessInfo.processInfo.environment["BERN_FRAME_LOCAL_EVENTS"] ?? ""
let localOwnActive13 = expectedOS == 13 && !ciHeartbeat && requestedLocalEvents == "own-pid-active13"
let sendsHeartbeat = ciHeartbeat || localOwnActive13''')
replace('var env = ProcessInfo.processInfo.environment, process: Process?, timer: Timer?, heartbeatError: String?, mainID: CGWindowID = 0',
        'var env = ProcessInfo.processInfo.environment, process: Process?, timer: Timer?, heartbeatError: String?, mainID: CGWindowID = 0\nvar activationRequests = [[String:Any]]()')
replace('"harness_sha":env["GITHUB_SHA"] ?? "local","expected_os":expectedOS,"os":ProcessInfo.processInfo.operatingSystemVersionString,',
        '"harness_sha":env["GITHUB_SHA"] ?? "local","expected_os":expectedOS,"os":ProcessInfo.processInfo.operatingSystemVersionString,\n    "deadline_seconds":75,"deadline_wall_time":deadline.timeIntervalSince1970,"frontmost_restore_rule":"Restore the captured immediate original PID only when own Gallery was still frontmost at teardown",')
replace('report["commands"] = commands; report["stages"] = stages; report["captures"] = captures; report["heartbeat_events"] = events',
        'report["commands"] = commands; report["stages"] = stages; report["captures"] = captures; report["heartbeat_events"] = events; report["activation_requests"] = activationRequests')
replace('func healthy(_ active: Bool = true) throws {', '''func requestActivation(_ pid: pid_t, options: NSApplication.ActivationOptions, names: [String], reason: String) {
    let before = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
    let accepted = NSRunningApplication(processIdentifier:pid)?.activate(options:options) ?? false
    activationRequests.append(["elapsed":Date().timeIntervalSince(began),"requested_pid":pid,"reason":reason,"options":names,"accepted":accepted,
        "frontmost_before":before,"frontmost_immediately_after":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0])
    try? save()
}
func healthy(_ active: Bool = true) throws {''')
replace('"interaction_scope":"Generated CLI and AXPress; CI own-PID mouseMoved keeps Frame awake. No physical input claim.",',
        '"interaction_scope":"Generated CLI and AXPress; explicit local13/CI own-active-PID mouseMoved keeps Frame awake. No physical input claim.",')
replace('"heartbeat_ci_only":ciHeartbeat,"frontmost_before":originalFront ?? 0,',
        '"heartbeat_ci_only":ciHeartbeat,"heartbeat_mode":sendsHeartbeat ? (localOwnActive13 ? "local-own-active13" : "ci-own-active") : "disabled","local_events_requested":requestedLocalEvents,"frontmost_before":originalFront ?? 0,')
replace('guard ciHeartbeat, heartbeatError == nil, let p = process, p.isRunning else { return }',
        'guard sendsHeartbeat, heartbeatError == nil, let p = process, p.isRunning else { return }')
replace('let r = bounds(w), point = CGPoint(x:r.midX,y:r.midY), local = CGPoint(x:r.width/2,y:r.height/2)',
        '''let r = bounds(w), point = CGPoint(x:r.midX,y:r.midY), local = CGPoint(x:r.width/2,y:r.height/2)
    guard r.width > 0, r.height > 0, (w[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue == true,
          ((w[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 else { heartbeatError = "Own active main window is not fully visible; heartbeat stopped"; return }''')
replace('try save(); try require(ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expectedOS,"Unexpected runtime OS")',
        '''try save(); try require(ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expectedOS,"Unexpected runtime OS")
    try require(requestedLocalEvents.isEmpty || localOwnActive13,"Local events require explicit own-pid-active13 on macOS13 outside CI")
    try require(sendsHeartbeat,"Requires CI mode or explicit local13 own-PID active mode; no CI impersonation")''')
replace('NSRunningApplication(processIdentifier:original)?.activate(options:[])',
        'requestActivation(original,options:[],names:[],reason:"restore-immediate-original-after-own-frontmost-teardown")')
old = '''    let ready = Date().addingTimeInterval(18)
    repeat { if let s = try cli(["sessions"],allowFailure:true) as? [[String:Any]], s.count == 1 { session = s[0]["session_id"] as? String ?? "" }; if session.isEmpty { try pause(0.1,active:false) } } while session.isEmpty && Date() < ready
    try require(!session.isEmpty,"Expected one UI session"); NSRunningApplication(processIdentifier:p.processIdentifier)?.activate(options:[.activateAllWindows,.activateIgnoringOtherApps])
    for _ in 0..<40 { if NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier, let w = ownWindows().filter({ ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 }).first { mainID = windowID(w); break }; try pause(0.05,active:false) }
    try require(mainID != 0,"No frontmost Gallery main window"); heartbeat(); timer = Timer.scheduledTimer(withTimeInterval:0.5,repeats:true) { _ in heartbeat() }'''
new = '''    let ready = min(deadline,Date().addingTimeInterval(18))
    repeat { if let s = try cli(["sessions"],allowFailure:true,until:ready) as? [[String:Any]], s.count == 1 { session = s[0]["session_id"] as? String ?? "" }; if session.isEmpty { try pause(0.1,active:false) } } while session.isEmpty && p.isRunning && Date() < ready
    try require(!session.isEmpty,"Expected one UI session")
    // Session transport is not UI readiness. No foreground request or control
    // inspection occurs before one main registry row and one visible own CG window.
    var startup = [[String:Any]](), startupID: CGWindowID = 0
    while p.isRunning && Date() < ready {
        let rows = try cli(["window","list"],session:true,allowFailure:true,until:ready) as? [[String:Any]] ?? []
        let mains = rows.filter { $0["kind"] as? String == "main" }
        let native = ownWindows().filter { ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 && bounds($0).height > 0 }
        startup.append(["elapsed":Date().timeIntervalSince(began),"deadline":ready.timeIntervalSince1970,"pid":p.processIdentifier,"windows":rows,"native_candidates":native])
        report["startup_readiness"] = startup; try save()
        if Date() < ready, mains.count == 1, native.count == 1, ((native[0][kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 { startupID = windowID(native[0]); break }
        try pause(min(0.08,max(0,ready.timeIntervalSinceNow)),active:false)
    }
    try require(startupID != 0,"Startup main registry and unique visible own CG window were not ready within18 seconds (individual CLI cap8 seconds)")
    requestActivation(p.processIdentifier,options:[.activateAllWindows,.activateIgnoringOtherApps],names:["activateAllWindows","activateIgnoringOtherApps"],reason:"own-gallery-after-startup-ready")
    for _ in 0..<40 {
        let native = ownWindows().filter { ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 && bounds($0).height > 0 }
        if NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier, native.count == 1, windowID(native[0]) == startupID { mainID = startupID; break }
        try pause(0.05,active:false)
    }
    try require(mainID != 0,"No frontmost Gallery main window matching the startup window"); heartbeat(); timer = Timer.scheduledTimer(withTimeInterval:0.5,repeats:true) { _ in heartbeat() }'''
replace(old, new)
(BASE / 'gallery-frame-reference.baseline.swift').write_text(baseline)
(BASE / 'gallery-frame-reference.swift').write_text(text)
(BASE / 'collector.patch').write_text(''.join(difflib.unified_diff(baseline.splitlines(keepends=True), text.splitlines(keepends=True),
    fromfile='a/gallery-frame-reference.swift', tofile='b/gallery-frame-reference.swift')))

manifest_path = WORKSPACE / 'outputs/macOS13/gallery-build.json'
manifest = json.loads(manifest_path.read_text())
assert manifest['source_sha'] == SOURCE and manifest['minimum_macos'] == '13.0'
assert sha(ORIGINAL_APP / 'Contents/MacOS/Gallery') == manifest['executable_sha256']
original_files = files(ORIGINAL_APP)
before = {'gui': macho(ORIGINAL_APP / 'Contents/MacOS/Gallery'), 'cli': macho(ORIGINAL_CLI)}
command(['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', str(ORIGINAL_APP)], 'original-gui-signature.log')
command(['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', str(ORIGINAL_CLI)], 'original-cli-signature.log')
entitlements = command(['/usr/bin/codesign', '-d', '--entitlements', '-', str(ORIGINAL_APP)], 'original-entitlements.log')
assert not entitlements.strip(), 'Preserve original entitlements before signing'
isolated = BASE / 'isolated'
assert not isolated.exists(), 'Never overwrite an existing isolated app'
copy_app = isolated / 'Gallery.app'
shutil.copytree(ORIGINAL_APP, copy_app, copy_function=shutil.copy2)
(isolated / 'bin').mkdir()
shutil.copy2(ORIGINAL_CLI, isolated / 'bin/gallery')
assert files(copy_app) == original_files
identifier = 'dev.bern.probe.frame13.f9.' + uuid.uuid4().hex[:12]
info_path = copy_app / 'Contents/Info.plist'
info = plistlib.loads(info_path.read_bytes())
original_identifier = info['CFBundleIdentifier']
info['CFBundleIdentifier'] = identifier
info_path.write_bytes(plistlib.dumps(info, sort_keys=False))
command(['/usr/bin/codesign', '--force', '--sign', '-', '--timestamp=none', '--identifier', identifier, str(copy_app)], 'copy-sign.log')
command(['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', str(copy_app)], 'copy-gui-signature.log')
command(['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', str(isolated / 'bin/gallery')], 'copy-cli-signature.log')
command(['/usr/bin/codesign', '-d', '--verbose=4', str(copy_app)], 'copy-gui-signature-details.log')
after = {'gui': macho(copy_app / 'Contents/MacOS/Gallery'), 'cli': macho(isolated / 'bin/gallery')}
assert before['gui']['sections'] == after['gui']['sections']
assert before['cli'] == after['cli']
assert files(ORIGINAL_APP) == original_files and sha(ORIGINAL_CLI) == before['cli']['sha256']
changed = sorted(p for p, h in files(copy_app).items() if original_files[p] != h)
assert set(changed) <= {'Contents/Info.plist', 'Contents/MacOS/Gallery', 'Contents/_CodeSignature/CodeResources'}
save('binary-comparison.json', {'original': before, 'isolated': after, 'all_sections_unchanged': True})
save('preparation.json', {'source_sha': SOURCE, 'source_build': manifest, 'source_manifest_sha256': sha(manifest_path),
    'source_collector_path': str(SOURCE_SCRIPT), 'source_collector_sha256': sha(SOURCE_SCRIPT),
    'collector_sha256': sha(BASE / 'gallery-frame-reference.swift'), 'collector_patch_sha256': sha(BASE / 'collector.patch'),
    'original_app': str(ORIGINAL_APP), 'original_cli': str(ORIGINAL_CLI), 'isolated_app': str(copy_app),
    'original_bundle_id': original_identifier, 'isolated_bundle_id': identifier, 'changed_copy_files': changed,
    'all_sections_unchanged': True, 'original_unchanged': True, 'strict_signatures_valid': True,
    'gui_or_cli_executed': False, 'ui_run': False, 'tcc_changes': False, 'main_product_changes': False})
print(json.dumps({'prepared': True, 'collector_sha256': sha(BASE / 'gallery-frame-reference.swift'),
                  'isolated_bundle_id': identifier, 'gui_sections': len(after['gui']['sections']),
                  'cli_sections': len(after['cli']['sections']), 'gui_sha256': after['gui']['sha256']}))
