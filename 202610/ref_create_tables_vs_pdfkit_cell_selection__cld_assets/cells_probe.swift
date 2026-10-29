import AppKit
import PDFKit
// Table-cell-selection probe. argv: OUT mode(on|off) waitSecs pdf targets.json
// Loads the PDF in an invisible PDFView, optionally disables private document analysis,
// waits for analysis, then for each target: (1) asks the page for tableSelectionFromPoint:toPoint:,
// (2) performs a synthesized exact drag and reports whether PDFView produced a text selection,
// a table-cell selection (isTableCellSelection), or nothing.
struct T: Decodable { let kind: String; let text: String }
let argv = CommandLine.arguments
let out = URL(fileURLWithPath: argv[1]); let mode = argv[2]; let wait = Double(argv[3])!
let mods: NSEvent.ModifierFlags = argv.count > 6 ? ["option": .option, "shift": .shift, "command": .command, "control": .control][argv[6]] ?? [] : []
var log = ""
func say(_ s: String) { log += s + "\n" }
let app = NSApplication.shared
app.setActivationPolicy(.accessory); app.finishLaunching()
DispatchQueue.main.asyncAfter(deadline: .now() + 600) { say("WATCHDOG"); try? log.write(to: out, atomically: true, encoding: .utf8); exit(3) }
let win = NSWindow(contentRect: NSRect(x: 40, y: 40, width: 700, height: 900), styleMask: [.borderless], backing: .buffered, defer: false)
win.alphaValue = 0; win.ignoresMouseEvents = true; win.isReleasedWhenClosed = false
let pdfView = PDFView(frame: win.contentView!.bounds)
pdfView.displayMode = .singlePage; pdfView.autoScales = false
win.contentView!.addSubview(pdfView); win.orderFrontRegardless()
func boolKey(_ o: NSObject, _ k: String) -> String { o.responds(to: Selector(k)) ? "\(o.value(forKey: k) ?? "nil")" : "n/a" }
say("defaults: documentAnalysisEnabled=\(boolKey(pdfView, "isDocumentAnalysisEnabled")) formDetectionEnabled=\(boolKey(pdfView, "isFormDetectionEnabled"))")
if mode == "markup" { pdfView.isInMarkupMode = true }
if mode == "off" {
  pdfView.setValue(false, forKey: "documentAnalysisEnabled")
  pdfView.setValue(false, forKey: "formDetectionEnabled")
}
say("markup=\(pdfView.isInMarkupMode) now: documentAnalysisEnabled=\(boolKey(pdfView, "isDocumentAnalysisEnabled")) formDetectionEnabled=\(boolKey(pdfView, "isFormDetectionEnabled"))")
let doc = PDFDocument(url: URL(fileURLWithPath: argv[4]))!, viewDoc = PDFDocument(url: URL(fileURLWithPath: argv[4]))!
let targets = try! JSONDecoder().decode([T].self, from: Data(contentsOf: URL(fileURLWithPath: argv[5])))
pdfView.document = viewDoc
pdfView.scaleFactor = 1.0
func drain(_ s: Double) { let u = Date().addingTimeInterval(s); while Date() < u { if let e = app.nextEvent(matching: .any, until: Date().addingTimeInterval(0.01), inMode: .default, dequeue: true) { app.sendEvent(e) } } }
func ev(_ t: NSEvent.EventType, _ p: NSPoint) -> NSEvent { NSEvent.mouseEvent(with: t, location: p, modifierFlags: mods, timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: win.windowNumber, context: nil, eventNumber: 0, clickCount: 1, pressure: t == .leftMouseUp ? 0 : 1)! }
typealias TableSelFn = @convention(c) (AnyObject, Selector, CGPoint, CGPoint) -> AnyObject?
let tsSel = Selector(("tableSelectionFromPoint:toPoint:"))
func tableSel(_ page: PDFPage, _ a: CGPoint, _ b: CGPoint) -> PDFSelection? {
  guard let m = class_getInstanceMethod(type(of: page), tsSel) else { return nil }
  let f = unsafeBitCast(method_getImplementation(m), to: TableSelFn.self)
  return f(page, tsSel, a, b) as? PDFSelection
}
func describe(_ s: PDFSelection?) -> String {
  guard let s = s else { return "nil" }
  let isCell = s.responds(to: Selector(("isTableCellSelection"))) ? "\(s.value(forKey: "isTableCellSelection") ?? "?")" : "n/a"
  let rect = s.responds(to: Selector(("tableCellSelectionRect"))) ? "\(s.value(forKey: "tableCellSelectionRect") ?? "?")" : "n/a"
  return "cell=\(isCell) rect=\(rect) str=«\((s.string ?? "nil").replacingOccurrences(of: "\n", with: "⏎").prefix(70))»"
}
// let analysis run
let pageCount = viewDoc.pageCount
for i in 0..<pageCount { pdfView.go(to: viewDoc.page(at: i)!); drain(wait / Double(pageCount)) }
for i in 0..<pageCount {
  let p = viewDoc.page(at: i)!
  say("page \(i+1): didPerformFormDetection=\(boolKey(p, "didPerformFormDetection")) containsDetectedFormFields=\(boolKey(p, "containsDetectedFormFields")) detectedAnnotations=\((p.value(forKey: "detectedAnnotations") as? [Any])?.count ?? -1)")
}
var tally: [String: Int] = [:]
for t in targets {
  let ws = t.text.split(separator: " ").map(String.init)
  if ws.count < 2 { continue }
  guard let s0 = doc.findString(ws.prefix(3).joined(separator: " "), withOptions: [.caseInsensitive]).first, let page = s0.pages.first else { continue }
  let r0 = s0.range(at: 0, on: page)
  let cands = (doc.findString(ws.suffix(min(2, ws.count - 1)).joined(separator: " "), withOptions: [.caseInsensitive]) + doc.findString(ws.last!, withOptions: [.caseInsensitive])).filter { $0.pages.first == page && $0.numberOfTextRanges(on: page) > 0 }
  guard let s1 = cands.filter({ $0.range(at: 0, on: page).location > r0.location }).sorted(by: { $0.range(at: 0, on: page).location < $1.range(at: 0, on: page).location }).first else { continue }
  let r1 = s1.range(at: s1.numberOfTextRanges(on: page) - 1, on: page)
  guard r1.location != NSNotFound, let sb0 = page.selection(for: NSRange(location: r0.location, length: 1)), let sb1 = page.selection(for: NSRange(location: r1.location + r1.length - 1, length: 1)) else { say("skip \(t.text)"); continue }
  let b0 = sb0.bounds(for: page), b1 = sb1.bounds(for: page)
  let vp = viewDoc.page(at: doc.index(for: page))!
  let pa = CGPoint(x: b0.minX + 0.6, y: b0.midY), pb = CGPoint(x: b1.maxX - 0.6, y: b1.midY)
  let ts = tableSel(vp, pa, pb)
  let pub = vp.selection(from: pa, to: pb)
  let pubGran = viewDoc.selection(from: vp, at: pa, to: vp, at: pb, with: .character)
  let wantP = t.text.lowercased().filter { $0.isLetter || $0.isNumber }
  func oc(_ x: PDFSelection?) -> String { let g = (x?.string ?? "").lowercased().filter { $0.isLetter || $0.isNumber }; let cell = (x?.value(forKey: "isTableCellSelection") as? Bool) ?? false; return x == nil ? "none" : (cell ? "TABLECELL" : (g == wantP ? "clean" : "other")) }
  tally["public-page/\(oc(pub))", default: 0] += 1
  tally["public-doc-granularity/\(oc(pubGran))", default: 0] += 1
  if pdfView.currentPage != vp { pdfView.go(to: vp); drain(0.3) }
  pdfView.scaleFactor = 1.0
  pdfView.clearSelection(); drain(0.6)
  let a = pdfView.convert(pdfView.convert(pa, from: vp), to: nil), b = pdfView.convert(pdfView.convert(pb, from: vp), to: nil)
  let inView = win.contentView!.bounds.contains(a) && win.contentView!.bounds.contains(b)
  for k in 1...6 { let f = CGFloat(k) / 6; DispatchQueue.main.asyncAfter(deadline: .now() + 0.03 * Double(k)) { app.postEvent(ev(.leftMouseDragged, NSPoint(x: a.x + (b.x - a.x) * f, y: a.y + (b.y - a.y) * f)), atStart: false) } }
  DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { app.postEvent(ev(.leftMouseUp, b), atStart: false) }
  win.sendEvent(ev(.leftMouseDown, a)); drain(0.5)
  let cur = pdfView.currentSelection
  let isCell = (cur?.responds(to: Selector(("isTableCellSelection"))) ?? false) ? ((cur?.value(forKey: "isTableCellSelection") as? Bool) ?? false) : false
  let want = t.text.lowercased().filter { $0.isLetter || $0.isNumber }
  let got = (cur?.string ?? "").lowercased().filter { $0.isLetter || $0.isNumber }
  let outcome = cur == nil ? "none" : (isCell ? "TABLECELL" : (got == want ? "clean" : (got.contains(want) ? "spill" : (want.contains(got) ? "short" : "wrong"))))
  tally["\(t.kind)/\(outcome)", default: 0] += 1
  let lines = cur?.selectionsByLine().map { let r = $0.bounds(for: vp); return r.minX.isFinite ? String(format: "%.0f,%.0f %.0fx%.0f", r.minX, r.minY, r.width, r.height) : "inf" }.joined(separator: " ; ") ?? "-"
  say("    byLine[\(cur?.selectionsByLine().count ?? 0)]: \(lines) | bounds=\(cur.map { "\($0.bounds(for: vp))" } ?? "-")")
  say("\(t.kind) inView=\(inView) drag=\(outcome) | tableSel: \(describe(ts)) | drag: \(describe(cur)) | \(t.text.prefix(36))")
}
say("TALLY \(tally.sorted { $0.key < $1.key })")
try? log.write(to: out, atomically: true, encoding: .utf8); exit(0)
