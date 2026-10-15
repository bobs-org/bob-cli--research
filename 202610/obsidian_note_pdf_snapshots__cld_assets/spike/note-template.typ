// Spike Typst template for Bob note snapshots (used via pandoc -t typst + raw header).
#let ink = rgb("#1F2328")
#let mute = rgb("#6E7781")
#let linkink = rgb("#2F5E96")
#let chipfill = rgb("#EEF1F4")
#let blue = rgb("#3B6EA8")
#let red = rgb("#B4443C")
#let green = rgb("#2E7D4F")

#set page(paper: "us-letter", margin: (x: 1in, top: 0.9in, bottom: 0.85in),
  footer: context [
    #set text(font: "Inter", size: 7.5pt, fill: mute)
    #if counter(page).get().first() > 1 [SHORTTITLE]
    #h(1fr)
    #counter(page).display("1 / 1", both: true)
  ])
#set text(font: ("Source Serif Pro", "Noto Color Emoji"), size: 10.5pt, fill: ink, lang: "en", hyphenate: false, ligatures: false)
#set par(justify: false, leading: 0.62em, spacing: 0.75em)
#show link: set text(fill: linkink)
#show raw: set text(font: ("Source Code Pro", "Noto Color Emoji"), size: 0.86em)
#show heading: set text(font: ("Inter", "Noto Color Emoji"))
#show heading.where(level: 1): it => block(above: 1.4em, below: 0.6em)[
  #set text(size: 15pt, weight: "bold")
  #it.body
  #v(-0.5em)
  #line(length: 100%, stroke: 1.2pt + chipfill)
]
#show heading.where(level: 2): it => block(above: 1.1em, below: 0.5em)[
  #set text(size: 9pt, weight: "bold", fill: mute, tracking: 0.04em)
  #upper(it.body)
]
#set list(indent: 0.2em, body-indent: 0.5em, marker: ([•], [–], [·]))
#show list: set text(fill: ink)

#let chip(body) = box(fill: chipfill, inset: (x: 3pt, y: 1.5pt), outset: (y: 1pt), radius: 2pt,
  text(font: "Inter", size: 7pt, fill: mute, body))
#let lab(body) = text(font: "Inter", size: 7pt, weight: "bold", fill: blue, tracking: 0.04em, upper(body)) + h(0.4em)
#let muted(body) = text(size: 0.9em, fill: mute, body)
#let glyph(st) = box(baseline: 0.12em, {
  let r = 0.42em
  if st == "open" { circle(radius: r, stroke: 0.7pt + mute) }
  else if st == "next" { circle(radius: r, stroke: 0.9pt + blue, align(center + horizon, circle(radius: 0.16em, fill: blue))) }
  else if st == "wip" { circle(radius: r, stroke: 0.8pt + blue, fill: gradient.linear((blue, 0%), (blue, 50%), (white, 50%), (white, 100%))) }
  else if st == "blocked" { circle(radius: r, stroke: 0.8pt + red, place(center + horizon, line(start: (-0.3em, 0.3em), end: (0.3em, -0.3em), stroke: 0.8pt + red))) }
  else if st == "done" { circle(radius: r, fill: green, align(center + horizon, text(fill: white, size: 0.6em, weight: "bold")[✓])) }
  else if st == "canceled" { circle(radius: r, stroke: 0.7pt + mute, align(center + horizon, text(fill: mute, size: 0.6em)[✕])) }
  else { text(fill: mute)[•] }
})
#let task(st, body) = (st, body)
#let tasks(..items) = block(spacing: 0.6em, {
  for (st, body) in items.pos() {
    grid(columns: (1.2em, 1fr), column-gutter: 0.3em, row-gutter: 0pt,
      align(left, glyph(st)), body)
    v(0.25em, weak: true)
  }
})

#let mastKicker(body) = text(font: "Inter", size: 7.5pt, weight: "bold", fill: blue, tracking: 0.12em, body) + parbreak()
#let mastTitle(body) = block(below: 0.6em, text(font: "Inter", size: 26pt, weight: "bold", body))
#let mastGoal(body) = block(below: 0.5em, text(size: 13pt, style: "italic", body))
#let mastGoalMeta(body) = block(below: 0.4em, text(font: "Inter", size: 8.5pt, fill: mute, body))
#let mastStats(body) = block(below: 0.4em, text(font: "Inter", size: 8.5pt, body))
#let mastNav(body) = block(below: 0.4em, text(font: "Inter", size: 8.5pt)[#text(fill: mute)[In this note:] #body])
#let mastSnapshot(body) = block(below: 0.4em, text(font: "Inter", size: 7.5pt, fill: mute, body))
#let mastrule = block(above: 0.6em, below: 0.9em, line(length: 100%, stroke: 1.2pt + chipfill))
