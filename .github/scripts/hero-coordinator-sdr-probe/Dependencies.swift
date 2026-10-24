// Diagnostic support only. Actual Motion and PictureHero are extracted separately.
import SwiftUI
import Combine

typealias BernObservableObject = Combine.ObservableObject
enum BernColor { case fixed(light: UInt32, dark: UInt32) }
