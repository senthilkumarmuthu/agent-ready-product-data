import json, glob, random, re, collections, sys
sys.path.insert(0, '.')
from measure import score, num, avail, gtin_ok, first, GT, brand_name
OUT = sys.argv[1]
site_n = collections.Counter(); res = []
for f in sorted(glob.glob('a24/*.json')):
    J = json.load(open(f)); res += J['reservoir']
    for k, c in J['sites'].items(): site_n[k.split('\t')[0]] += c['n']
def band(n): return 0 if n == 1 else 1 if n <= 10 else 2 if n <= 100 else 3 if n <= 1000 else 4
rng = random.Random(20261120)
rng.shuffle(res)
by = collections.defaultdict(list); seen = set()
for r in res:
    if r['pld'] in seen or not score(r)['core']: continue
    seen.add(r['pld']); by[band(site_n[r['pld']])].append(r)
avail_n = {b: len(v) for b, v in by.items()}
# equal allocation of 120 per band, shortfall topped up from the larger bands in order
take = {b: min(120, len(by[b])) for b in range(5)}; short = 600 - sum(take.values())
for b in (4, 3, 2, 1, 0):
    add = min(short, len(by[b]) - take[b]); take[b] += add; short -= add
recs = [r for b in range(5) for r in by[b][:take[b]]]
def trim(v):
    return v[:300] if isinstance(v, str) else v
def jsonld(r, drop=(), conflict=False):
    p = r['p']; d = {'@context': 'https://schema.org', '@type': 'Product'}
    for k in ('name', 'description', 'sku', 'brand') + GT + ('mpn', 'image'):
        if k in drop or k not in p: continue
        v = [x for x in p[k] if x]
        if not v: continue
        if k == 'brand':
            b = brand_name(p['brand'])
            if b: d['brand'] = {'@type': 'Brand', 'name': b}
            continue
        d[k] = trim(v[0])
    offs = []
    for o in r['offers']:
        od = {'@type': 'Offer'}
        pr = first(o.get('price')) or first(o.get('lowPrice'))
        cu = first(o.get('priceCurrency'))
        if not pr:
            for ps in o.get('priceSpecification', []):
                if isinstance(ps, dict) and first(ps.get('price')): pr = first(ps.get('price')); cu = cu or first(ps.get('priceCurrency')); break
        if pr and 'price' not in drop: od['price'] = pr
        if cu and 'price' not in drop: od['priceCurrency'] = cu
        av = first(o.get('availability'))
        if av and 'availability' not in drop: od['availability'] = av
        for k in GT + ('mpn',):
            if k not in drop and first(o.get(k)): od[k] = first(o.get(k))
        if first(o.get('sku')): od['sku'] = first(o.get('sku'))
        if len(od) > 1: offs.append(od)
    if conflict and offs:
        o2 = dict(offs[0]); o2['availability'] = 'https://schema.org/OutOfStock'; offs[0]['availability'] = 'https://schema.org/InStock'
        if 'sku' not in o2 and first(p.get('sku')): o2['sku'] = offs[0]['sku'] = first(p.get('sku'))
        offs.append(o2)
    if offs: d['offers'] = offs if len(offs) > 1 else offs[0]
    return d
def truth(r):
    prices = set(); stock = set()
    for o in r['offers']:
        pr = first(o.get('price')) or first(o.get('lowPrice')); cu = first(o.get('priceCurrency'))
        if not pr:
            for ps in o.get('priceSpecification', []):
                if isinstance(ps, dict) and first(ps.get('price')): pr = first(ps.get('price')); cu = cu or first(ps.get('priceCurrency')); break
        if num(pr) and cu: prices.add((round(num(pr), 2), cu.strip().upper()))
        a = avail(first(o.get('availability')))
        if a: stock.add(a in ('InStock', 'LimitedAvailability', 'OnlineOnly', 'InStoreOnly'))
    ids = set()
    for k in GT + ('mpn',):
        for v in (r['p'].get(k, []) + [x for o in r['offers'] for x in o.get(k, [])]):
            if isinstance(v, str) and v.strip(): ids.add(re.sub(r'[\s\-]', '', v.strip()).lower())
    return {'prices': sorted(prices), 'stock': sorted(stock), 'ids': sorted(ids)}
Q = {'price': 'What does this cost, in what currency?', 'stock': 'Can I buy this today?', 'id': "What is this product's GTIN or manufacturer part number?"}
items = []; truths = {}
for i, r in enumerate(recs):
    rid = f'r{i:03d}'; truths[rid] = truth(r) | {'band': band(site_n[r['pld']])}
    conds = [('c1_complete', (), False, ['price', 'stock', 'id']), ('c2_no_price', ('price',), False, ['price']),
             ('c3_no_availability', ('availability',), False, ['stock']), ('c4_no_identifier', GT + ('mpn',), False, ['id']),
             ('c5_conflicting_availability', (), True, ['stock'])]
    for c, drop, conf, qs in conds:
        doc = json.dumps(jsonld(r, drop, conf), ensure_ascii=False)
        for q in qs: items.append({'id': f'{rid}_{c}_{q}', 'rec': rid, 'cond': c, 'q': q, 'question': Q[q], 'jsonld': doc})
json.dump(truths, open(OUT + '/probe_truth.json', 'w'), ensure_ascii=False)
with open(OUT + '/probe_items.jsonl', 'w') as f:
    for it in items: f.write(json.dumps(it, ensure_ascii=False) + '\n')
print('reserve', len(res), 'available per band', avail_n, 'taken', take, 'records', len(recs), 'items', len(items))
print('truth: stock known', sum(1 for t in truths.values() if t['stock']), 'stock ambiguous', sum(1 for t in truths.values() if len(t['stock']) > 1))
