// Tách nền ảnh bằng Apple Vision (macOS 14+): giữ người/vật nổi bật, ghi PNG trong suốt, cắt sát vật.
// Dùng: cutout <ảnh vào> <png ra> [--largest]   — mã thoát 2 nếu không tìm thấy vật nổi bật.
// --largest: chỉ giữ một vật/người lớn nhất (cutout một nhân vật được nhắc tên).
import AppKit
import CoreImage
import Vision

let args = CommandLine.arguments
let largest = args.contains("--largest")
let paths = args.filter { $0 != "--largest" }
guard paths.count == 3, let input = CIImage(contentsOf: URL(fileURLWithPath: paths[1])) else {
    FileHandle.standardError.write("cách dùng: cutout <ảnh vào> <png ra>\n".data(using: .utf8)!); exit(1)
}
let handler = VNImageRequestHandler(ciImage: input)
let request = VNGenerateForegroundInstanceMaskRequest()
do { try handler.perform([request]) } catch { FileHandle.standardError.write("Vision lỗi: \(error)\n".data(using: .utf8)!); exit(1) }
guard let result = request.results?.first, !result.allInstances.isEmpty else { exit(2) }
func area(_ instance: Int) -> Int {
    guard let mask = try? result.generateScaledMaskForImage(forInstances: [instance], from: handler) else { return 0 }
    CVPixelBufferLockBaseAddress(mask, .readOnly); defer { CVPixelBufferUnlockBaseAddress(mask, .readOnly) }
    let width = CVPixelBufferGetWidth(mask), height = CVPixelBufferGetHeight(mask), stride = CVPixelBufferGetBytesPerRow(mask)
    let base = CVPixelBufferGetBaseAddress(mask)!.assumingMemoryBound(to: Float32.self)
    var count = 0
    for y in Swift.stride(from: 0, to: height, by: 4) { for x in Swift.stride(from: 0, to: width, by: 4) {
        if base[y * stride / 4 + x] > 0.5 { count += 1 } } }
    return count
}
let chosen: IndexSet = largest ? IndexSet(integer: result.allInstances.max(by: { area($0) < area($1) })!) : result.allInstances
do {
    let buffer = try result.generateMaskedImage(ofInstances: chosen, from: handler, croppedToInstancesExtent: true)
    let image = CIImage(cvPixelBuffer: buffer)
    let context = CIContext()
    guard let cg = context.createCGImage(image, from: image.extent) else { exit(1) }
    let rep = NSBitmapImageRep(cgImage: cg)
    try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: paths[2]))
    print("\(cg.width)x\(cg.height)")
} catch { FileHandle.standardError.write("ghi lỗi: \(error)\n".data(using: .utf8)!); exit(1) }
