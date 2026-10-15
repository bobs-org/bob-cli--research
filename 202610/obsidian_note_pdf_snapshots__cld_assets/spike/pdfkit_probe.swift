// Spike: what text does PDFKit (the framework Highlights uses) return for each line of a PDF?
// Usage: swift pdfkit_probe.swift vocab.txt a.pdf [b.pdf ...]
// For each PDF, selects every line on every page (selectionsByLine), tokenizes the line
// strings, and counts tokens that are not words of the source text (merged or split words).
import Foundation
import PDFKit

let args = CommandLine.arguments
let vocabText = try! String(contentsOfFile: args[1], encoding: .utf8)
func words(_ s: String) -> [String] {
    s.lowercased().components(separatedBy: CharacterSet.letters.inverted).filter { $0.count >= 2 }
}
let vocab = Set(words(vocabText))

for path in args.dropFirst(2) {
    guard let doc = PDFDocument(url: URL(fileURLWithPath: path)) else { print("\(path): cannot open"); continue }
    var total = 0, unknown: [String: Int] = [:], lines = 0
    for i in 0..<doc.pageCount {
        guard let page = doc.page(at: i), let sel = page.selection(for: page.bounds(for: .mediaBox)) else { continue }
        for line in sel.selectionsByLine() {
            lines += 1
            for w in words(line.string ?? "") {
                total += 1
                if !vocab.contains(w) { unknown[w, default: 0] += 1 }
            }
        }
    }
    let bad = unknown.values.reduce(0, +)
    let sample = unknown.sorted { $0.value > $1.value }.prefix(14).map { "\($0.key)" }.joined(separator: " ")
    print(String(format: "%@\tlines=%d tokens=%d unknown=%d (%.2f%%)\t%@", (path as NSString).lastPathComponent, lines, total, bad, 100.0 * Double(bad) / Double(max(total, 1)), sample))
}
