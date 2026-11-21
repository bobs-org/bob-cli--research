import json, re, sys, unicodedata, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36'
def get(url, timeout=40):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.read()
def episode_id(raw):
    u = urllib.parse.urlsplit(raw)
    if raw.startswith('spotify:episode:'): return raw.split(':')[2]
    m = re.search(r'/episode/([0-9A-Za-z]{22})', u.path)
    return m.group(1) if m else None
def norm(t):
    t = unicodedata.normalize('NFKD', t).lower()
    t = re.sub(r'[^a-z0-9]+', ' ', t)
    return ' '.join(t.split())
def embed(eid):
    _, b = get(f'https://open.spotify.com/embed/episode/{eid}')
    m = re.search(rb'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', b, re.S)
    e = json.loads(m.group(1))['props']['pageProps']['state']['data']['entity']
    return e
def itunes(show):
    q = urllib.parse.urlencode({'term': show, 'media': 'podcast', 'entity': 'podcast', 'limit': 10})
    _, b = get('https://itunes.apple.com/search?' + q)
    return json.loads(b)['results']
def main(raw):
    eid = episode_id(raw)
    e = embed(eid)
    title, show = e['title'], e['subtitle']
    rel = datetime.fromisoformat(e['releaseDate']['isoString'].replace('Z', '+00:00'))
    dur = e['duration'] / 1000
    out = {'id': eid, 'title': title, 'show': show, 'released': rel.isoformat(), 'duration_s': round(dur)}
    cands = [r for r in itunes(show) if norm(r.get('collectionName', '')) == norm(show) and r.get('feedUrl')]
    out['itunes_exact_show_matches'] = len(cands)
    best = None
    for c in cands[:3]:
        try:
            _, b = get(c['feedUrl'], 60)
            ch = ET.fromstring(b).find('channel')
        except Exception as ex:
            out.setdefault('feed_errors', []).append(str(ex)[:80]); continue
        for it in ch.findall('item'):
            t = it.findtext('title') or ''
            try:
                pd = parsedate_to_datetime(it.findtext("pubDate"))
                pd = pd if pd.tzinfo else pd.replace(tzinfo=timezone.utc)
            except Exception: pd = None
            d = it.findtext('{http://www.itunes.com/dtds/podcast-1.0.dtd}duration') or ''
            try:
                parts = [float(x) for x in d.split(':')]
                ds = sum(p * 60 ** i for i, p in enumerate(reversed(parts)))
            except Exception: ds = None
            score = []
            if norm(t) == norm(title): score.append('title=')
            if pd and abs((pd - rel).total_seconds()) < 36 * 3600: score.append('date±36h')
            if ds and abs(ds - dur) <= max(5, 0.02 * dur): score.append('dur±2%')
            if len(score) >= 2 and (best is None or len(score) > len(best[0])):
                tr = [x.attrib for x in it.findall('{https://podcastindex.org/namespace/1.0}transcript')]
                chap = it.find('{https://podcastindex.org/namespace/1.0}chapters')
                desc = it.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or it.findtext('description') or ''
                best = (score, {'feed': c['feedUrl'], 'item_title': t, 'signals': score,
                         'transcripts': [(a.get('type'), a.get('url', '')[:60]) for a in tr],
                         'chapters_tag': chap.attrib.get('url', '')[:60] if chap is not None else None,
                         'desc_chars': len(desc), 'has_timestamps_in_desc': bool(re.search(r'\b\d{1,2}:\d{2}(:\d{2})?\b', desc)),
                         'enclosure': (it.find('enclosure').attrib.get('type') if it.find('enclosure') is not None else None)})
    out['match'] = best[1] if best else None
    print(json.dumps(out, indent=1))
for a in sys.argv[1:]:
    try: main(a)
    except Exception as ex: print(a, 'ERROR', repr(ex)[:200])
