import Foundation
import PDFKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let doc = PDFDocument(url: url) else { print("cannot open"); exit(1) }
for i in 0..<doc.pageCount {
  guard let page = doc.page(at: i) else { continue }
  print("=== page \(i+1) page.string ===")
  print(page.string ?? "<nil>")
  print("=== page \(i+1) selection(for: bounds).string ===")
  print(page.selection(for: page.bounds(for: .mediaBox))?.string ?? "<nil>")
  for a in page.annotations where a.type == "Link" {
    var d = ""
    if let g = a.action as? PDFActionGoTo { d = "GoTo page=\(g.destination.page.map { doc.index(for: $0) + 1 } ?? -1) point=\(g.destination.point)" }
    else if let dest = a.destination { d = "dest page=\(dest.page.map { doc.index(for: $0) + 1 } ?? -1) point=\(dest.point)" }
    else if let u = a.action as? PDFActionURL { d = "URL \(u.url?.absoluteString ?? "")" }
    print("link bounds=\(a.bounds) \(d)")
  }
}
