import sys, json, random, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import score
# usage: agg.py input(.gz quads | .jsonl records) out.json crawl
src, out, crawl = sys.argv[1], sys.argv[2], sys.argv[3]
def records():
    if src.endswith('.jsonl'):
        for l in open(src): yield json.loads(l)
    else:
        import parse
        from parse import pages, page_graph
        import io, contextlib
        tmp = io.StringIO()
        # reuse parse.py main logic via a generator
        for rec in parse.records(src): yield rec
site = collections.defaultdict(lambda: collections.Counter())
res = []; rng = random.Random(sum(map(ord, os.path.basename(src))) * 7919 + 20261120); seen = 0
for r in records():
    s = score(r, crawl)
    key = r['pld'] + '\t' + ('md' if r['md'] else 'jl') + '\t' + ('nest' if r['nested'] else 'top')
    c = site[key]; c['n'] += 1
    for k, v in s.items():
        if isinstance(v, bool) and v: c[k] += 1
    if s['core'] and not r['nested']:
        seen += 1
        if len(res) < 100: res.append(r)
        else:
            j = rng.randrange(seen)
            if j < 100: res[j] = r
json.dump({'sites': {k: dict(v) for k, v in site.items()}, 'reservoir': res}, open(out, 'w'))
print(len(site), sum(v['n'] for v in site.values()))
