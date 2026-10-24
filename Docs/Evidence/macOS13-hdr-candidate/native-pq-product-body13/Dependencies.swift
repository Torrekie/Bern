// Diagnostic dependencies only. The image renderer/cache/body are the product slice.
import SwiftUI
import Combine

typealias BernObservableObject = ObservableObject
struct BernMotion {let period:Double;let damping:Double}
enum BernColor {case fixed(light:UInt32,dark:UInt32)}
// Hero is deliberately excluded; no snapshot, overlay or animation is tested.
struct BernPictureHero:ViewModifier {
    let id:String?
    let picture:BernImage.Picture?
    let fit:BernImageFit
    let corner:CGFloat
    let motion:BernMotion
    func body(content:Content)->some View {content}
}
