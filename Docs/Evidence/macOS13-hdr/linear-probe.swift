import AppKit
import CoreImage
import ImageIO
let source=CGImageSourceCreateWithURL(URL(fileURLWithPath:CommandLine.arguments[1]) as CFURL,nil)!
let image=CGImageSourceCreateImageAtIndex(source,0,nil)!
let floating=CGImageSourceCreateImageAtIndex(source,0,[kCGImageSourceShouldAllowFloat:true] as CFDictionary)!
let pq=CGColorSpace(name:CGColorSpace.itur_2100_PQ)!
let spaces:[(String,CGColorSpace)] = [("linear-sRGB",CGColorSpace(name:CGColorSpace.extendedLinearSRGB)!), ("linear-2020",CGColorSpace(name:CGColorSpace.extendedLinearITUR_2020)!), ("linear-P3",CGColorSpace(name:CGColorSpace.extendedLinearDisplayP3)!)] + [("linearized-original",CGColorSpaceCreateExtendedLinearized(image.colorSpace!)),("linearized-PQ",CGColorSpaceCreateExtendedLinearized(pq))].compactMap{ name,space in space.map{(name,$0)}}
for (name,img) in [("original",image),("named-PQ",image.copy(colorSpace:pq)!),("ImageIO-allow-float",floating)] {
 print("image",name,"bits",img.bitsPerComponent,"float",img.bitmapInfo.contains(.floatComponents),"cs",img.colorSpace?.name as Any)
 for (spacename,space) in spaces {
  let cg=CGContext(data:nil,width:640,height:360,bitsPerComponent:32,bytesPerRow:640*16,space:space,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.floatComponents.rawValue|CGBitmapInfo.byteOrder32Little.rawValue)!
  cg.draw(img,in:CGRect(x:0,y:0,width:640,height:360))
  let floats=cg.data!.assumingMemoryBound(to:Float.self)
  let cgvalues=[floats[(100*640+100)*4],floats[(100*640+500)*4],floats[(260*640+100)*4],floats[(260*640+500)*4]]
  for working in [false,true] {
   let context=CIContext(options:working ? [.workingColorSpace:space]:[:])
   let input=CIImage(cgImage:img)
   var vals:[Float]=[]
   for x in [100,500] {
    var p=[Float](repeating:0,count:4)
    context.render(input,toBitmap:&p,rowBytes:16,bounds:CGRect(x:x,y:260,width:1,height:1),format:.RGBAf,colorSpace:space)
    vals.append(p[0])
   }
   print(name,spacename,"CG",cgvalues,"CI-working-explicit",working,vals)
  }
 }
}
