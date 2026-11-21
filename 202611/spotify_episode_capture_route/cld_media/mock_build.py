"""Build a design mock of the proposed podcast-episode reference PDF (HTML)."""
import html, json, re, sys
from html.parser import HTMLParser
from datetime import datetime
import xml.etree.ElementTree as ET

DATA, NET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
emb = open(f'{DATA}/embed.html', encoding='utf-8').read()
ent = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', emb, re.S).group(1))['props']['pageProps']['state']['data']['entity']
ch = ET.parse(f'{NET}/feed.rss').getroot().find('channel')
host = ch.findtext('{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
item = next(i for i in ch.findall('item') if i.findtext('title') == ent['title'])
desc = item.findtext('description')
vtt = open(f'{NET}/t.vtt', encoding='utf-8').read()

def ts(s):
    p = s.split(':'); p = ['0'] * (3 - len(p)) + p
    return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
def fmt(sec):
    sec = int(sec); h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'

# --- chapters from show notes, and show notes without the duplicate timestamp block
chapters = []
class Notes(HTMLParser):
    KEEP = {'p', 'a', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'br', 'blockquote'}
    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in self.KEEP:
            if tag == 'a':
                href = dict(attrs).get('href', '')
                self.out.append(f'<a href="{html.escape(href)}">' if href.startswith(('http://', 'https://')) else '<a>')
            else:
                self.out.append(f'<{tag}>')
    def handle_endtag(self, tag):
        if tag in self.KEEP and tag != 'br': self.out.append(f'</{tag}>')
    def handle_data(self, data): self.out.append(html.escape(data))
n = Notes(); n.feed(desc); notes = ''.join(n.out)
paras = re.findall(r'<p>.*?</p>', notes, re.S)
kept = []
for p in paras:
    text = re.sub(r'<[^>]+>', '', html.unescape(p)).strip()
    m = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$', text)
    if m:
        chapters.append((ts(m.group(1)), m.group(1), m.group(2))); continue
    if text.lower() in ('timestamps', 'chapters'): continue
    if not text or text in ('—', '–'): kept.append('<hr>'); continue
    kept.append(p)
notes = '\n'.join(kept).replace('<p><strong></strong></p>', '')

# --- transcript cues -> turns -> paragraphs
cues = []
for block in re.split(r'\n\s*\n', vtt):
    m = re.search(r'(\d[\d:.]+)\s+-->\s+(\d[\d:.]+)', block)
    if not m: continue
    t = block[m.end():].strip()
    sp = re.match(r'<v ([^>]+)>', t)
    cues.append((ts(m.group(1)), sp.group(1) if sp else '?', re.sub(r'<[^>]+>', '', t).replace('\n', ' ').strip()))
turns = []
for start, sp, text in cues:
    if turns and turns[-1]['sp'] == sp: turns[-1]['cues'].append((start, text))
    else: turns.append({'sp': sp, 'cues': [(start, text)]})
# roles from interviewer signal (questions), names never guessed
q, cnt = {}, {}
for tu in turns:
    txt = ' '.join(c[1] for c in tu['cues']); cnt[tu['sp']] = cnt.get(tu['sp'], 0) + 1
    q[tu['sp']] = q.get(tu['sp'], 0) + txt.rstrip().endswith('?')
ranked = sorted(cnt, key=lambda s: q[s] / cnt[s], reverse=True)
roles = {}
if len(cnt) == 2 and q[ranked[0]] >= 10 and q[ranked[0]] / cnt[ranked[0]] >= 3 * max(q[ranked[1]] / cnt[ranked[1]], 0.01):
    roles = {ranked[0]: 'Host', ranked[1]: 'Guest'}
else:
    order = []
    for tu in turns:
        if tu['sp'] not in order: order.append(tu['sp'])
    roles = {s: f'Speaker {i+1}' for i, s in enumerate(order)}
paragraphs = []
for tu in turns:
    cur, first = [], True
    for start, text in tu['cues']:
        if not cur: pstart = start
        cur.append(text)
        words = sum(len(x.split()) for x in cur)
        if words >= 95 and re.search(r'[.?!]["”]?$', text):
            paragraphs.append({'t': pstart, 'sp': tu['sp'], 'new': first, 'text': ' '.join(cur)}); cur, first = [], False
    if cur: paragraphs.append({'t': pstart, 'sp': tu['sp'], 'new': first, 'text': ' '.join(cur)})
# chapter -> paragraph: nearest paragraph start within 30s, else next paragraph after
chap_at = {}
for i, (sec, label, title) in enumerate(chapters):
    near = [j for j, p in enumerate(paragraphs) if abs(p['t'] - sec) <= 30]
    j = min(near, key=lambda j: abs(paragraphs[j]['t'] - sec)) if near else next((j for j, p in enumerate(paragraphs) if p['t'] >= sec), None)
    if j is not None and j not in chap_at: chap_at[j] = (i, label, title)

words = sum(len(p['text'].split()) for p in paragraphs)
dur = ent['duration'] / 1000
dur_s = f"{int(dur // 3600)} hr {round(dur % 3600 / 60)} min" if dur >= 3600 else f"{round(dur / 60)} min"
rel = datetime.fromisoformat(ent['releaseDate']['isoString'].replace('Z', '+00:00'))
date_s = rel.strftime('%A, %B %-d, %Y')
canon = f"https://open.spotify.com/episode/{ent['id']}"
title, show = ent['title'], ent['subtitle']
E = html.escape

chap_rows = ''.join(f'<li><a href="#ch{i}"><span class="t">{E(label)}</span><span class="c">{E(t)}</span></a></li>' for i, (_, label, t) in enumerate(chapters))
body = []
for j, p in enumerate(paragraphs):
    if j in chap_at:
        i, label, t = chap_at[j]
        body.append(f'<h3 id="ch{i}" class="chapter"><span class="gutter">{E(label)}</span>{E(t)}</h3>')
    role = roles[p['sp']]
    cls = 'host' if role == 'Host' else ('guest' if role == 'Guest' else 'spk')
    label = f'<span class="who {cls}">{E(role)}</span> ' if p['new'] else ''
    body.append(f'<p class="turn{" first" if p["new"] else ""}"><span class="gutter">{fmt(p["t"])}</span>{label}{E(p["text"])}</p>')

page = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{E(title)}</title>
<link rel="stylesheet" href="reader.css"><link rel="stylesheet" href="podcast.css">
<style>@page {{ @bottom-left {{ content: "{E(title)}"; }} }} @page :first {{ @bottom-left {{ content: none; }} }}</style></head><body>
<header class="ep">
  <p class="masthead-site">Podcast episode · {E(show)}</p>
  <div class="ep-hero">
    <img class="ep-art" src="cover.jpg" alt="">
    <div class="ep-id">
      <h1 class="masthead-title">{E(title)}</h1>
      <p class="ep-by"><strong>{E(show)}</strong> · Hosted by {E(host)}</p>
      <p class="ep-meta">{E(date_s)} · {dur_s}</p>
      <p class="ep-pills"><a class="pill play" href="{canon}">▶&#xFE0E; Listen on Spotify</a><span class="pill">{len(chapters)} chapters</span><span class="pill">Transcript · {words/1000:.1f}k words</span></p>
    </div>
  </div>
  <p class="masthead-provenance"><span><a href="{canon}">{canon}</a></span> · <span>Captured November 21, 2026</span></p>
</header>
<section class="chapters"><h2>Chapters</h2><ol>{chap_rows}</ol></section>
<section class="notes"><h2>Show notes</h2>{notes}</section>
<section class="transcript"><h2>Transcript</h2>
<p class="tx-note">Publisher transcript from the show’s RSS feed · {len(cnt)} speakers · roles inferred, names not guessed · chapter marks placed at the nearest paragraph (± 30 s)</p>
{''.join(body)}
</section></body></html>'''
open(f'{OUT}/episode.html', 'w', encoding='utf-8').write(page)
print('chapters', len(chapters), 'placed', len(chap_at), 'paragraphs', len(paragraphs), 'words', words, 'roles', roles)
