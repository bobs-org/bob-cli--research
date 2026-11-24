"""Prototype: Wispr Flow plain-text summary -> Bob meeting-notes Markdown.

Heuristic (deterministic, no LLM):
- blocks are separated by blank lines; a run of >=2 blank lines starts a new section
- first block = TL;DR headline
- a section's first block is its heading when it is one short line with no
  terminal punctuation
- other blocks become bullets; "(Owner) Action" lines under a Next Steps
  heading become an owner/action table
"""
import re, sys

src, title, when, event, area = sys.argv[1:6]
text = open(src, encoding="utf-8").read().replace("\r\n", "\n").strip("\n")
sections = re.split(r"\n{3,}", text)
headline = sections[0].strip()
out = [
    "---", f'title: "{title}"', "---", "",
    f"# {title}", "",
    "| | |", "|---|---|",
    f"| **When** | {when} |",
    f"| **Event** | {event} |",
    f"| **Area** | {area} |",
    "| **Source** | Wispr Flow Notetaker summary |", "",
    "> [!summary] TL;DR", f"> {headline}", "",
]
for sec in sections[1:]:
    blocks = [b.strip() for b in sec.split("\n\n") if b.strip()]
    head, body = blocks[0], blocks[1:]
    if "\n" in head or len(head) > 80 or head[-1] in ".;:!?":
        head, body = None, blocks
    if head:
        out += [f"## {head}", ""]
    actions = [re.match(r"^\((?P<who>[^)]+)\)\s*(?P<what>.+)$", b, re.S) for b in body]
    if head and re.search(r"next steps|action items", head, re.I) and all(actions):
        out += ["| Owner | Action |", "|---|---|"]
        out += [f"| {m['who']} | {m['what']} |" for m in actions]
    else:
        out += [f"- {b}" for b in body]
    out.append("")
print("\n".join(out))
