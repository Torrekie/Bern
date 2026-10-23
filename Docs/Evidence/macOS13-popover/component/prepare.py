from pathlib import Path
import hashlib,json,sys
here=Path(__file__).resolve().parent
repo=next(p for p in here.parents if (p/'crates/bern-backend-swiftui/templates/BernStyle.swift').is_file())
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()/'work/volume-popover-reproduction'
out.mkdir(parents=True,exist_ok=True)
style=(repo/'crates/bern-backend-swiftui/templates/BernStyle.swift').read_text()
appkit=(repo/'crates/bern-backend-swiftui/templates/BernAppKit.swift').read_text()
runtime=(repo/'crates/bern-backend-swiftui/templates/BernRuntime.swift').read_text()
def decl(source,needle):
 start=source.index(needle)
 i=source.index('{',start)
 depth=1;j=i+1
 while depth:
  if source[j]=='{':depth+=1
  elif source[j]=='}':depth-=1
  j+=1
 return source[start:j]
def extension(source,needle): return 'extension View {\n'+decl(source,needle)+'\n}\n'
parts=['import AppKit\nimport SwiftUI\nimport Combine\nimport CryptoKit\nimport ImageIO\n']
parts += [decl(style,'enum BernButtonLook')]
parts += [extension(style,'func bernButtonLook(_ look:')]
for t in ['private struct BernControlGroupHeightKey','private struct BernOnBarKey']:
 parts += [decl(style,t)]
parts += ['extension EnvironmentValues { var bernControlGroupHeight: CGFloat? { get {self[BernControlGroupHeightKey.self]} set {self[BernControlGroupHeightKey.self]=newValue} }; var bernOnBar: Bool {get {self[BernOnBarKey.self]} set {self[BernOnBarKey.self]=newValue}} }']
parts += ['@MainActor final class BernThemeState: ObservableObject { static let shared=BernThemeState() }; struct BernColor { var color: Color; static func role(_ name:String)->BernColor {BernColor(color:.white)} }']
parts += ['extension EnvironmentValues { var bernSceneScaled: Bool {false}; var bernAccent: Color? {nil} }; extension View {func bernPrimaryLabel()->some View {self};func bernAccentTint()->some View {self}}']
# Only SDK26 branch spelling is adapted for the old compiler. That branch is
# never executed on13; all active13 style, trigger, popover and bridge code is extracted.
look=decl(style,'private struct BernSystemButtonLook:')
look=look.replace('.buttonStyle(.glassProminent)','.buttonStyle(.borderedProminent)').replace('.buttonStyle(.glass)','.buttonStyle(.bordered)')
parts += [look,decl(style,'private struct BernGroupedButtonStyle:'),decl(style,'private struct BernLegacyShapedButton:'),extension(style,'@ViewBuilder func bernCircleBorderShape()')]
parts += ['@MainActor\n'+decl(appkit,'struct BernCircularIconButton<'), '@MainActor\n'+decl(appkit,'private struct BernCircularIconControl:')]
parts += [runtime[runtime.index('struct BernControlActions {'):runtime.index('/// Chooses one layout by the available width.')]]
parts += [extension(runtime,'func bernControl(')]
parts += ['@MainActor final class BernWindowContext: ObservableObject {let id="fixture"};@MainActor final class BernHost {static let shared=BernHost();let controls=BernControls();func isBlocked(_ id:String)->Bool{false}}']
parts += ['extension View {func bernOnChange<V:Equatable>(of value:V,_ action:@escaping()->Void)->some View {onChange(of:value){_ in action()}}}']
parts += [extension(style,'@ViewBuilder func bernPopover<Content:'),extension(style,'@ViewBuilder fileprivate func bernPopoverMaterial('),decl(style,'struct BernPopoverButton<')]
parts += [(Path(__file__).parent/'fixture-tail.swift').read_text()]
output=out/'VolumePopoverProbe.swift'
joined='\n\n'.join(parts)+'\n'
output.write_text(joined)
(out/'extraction.json').write_text(json.dumps({'product_files':[{'path':str(repo/'crates/bern-backend-swiftui/templates'/name),'sha256':hashlib.sha256((repo/'crates/bern-backend-swiftui/templates'/name).read_bytes()).hexdigest()} for name in ['BernStyle.swift','BernAppKit.swift','BernRuntime.swift']], 'adaptations':['Unused SDK26 glass type names replaced by corresponding pre26 style names solely to typecheck on SDK14.2; branch not executed on13.','Unrelated theme/host types are minimal fixture adapters.','Popover, native circular bridge, control registry and mount modifier extracted verbatim.']},indent=2)+'\n')
print(output)
