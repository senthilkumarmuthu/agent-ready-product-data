import sys, gzip, re, json, collections
from urllib.parse import urlsplit
Q = re.compile(r'^(\S+) <([^>]+)> (.+) <([^>]*)>\s+\.\s*$')
S = ('http://schema.org/','https://schema.org/')
import os
LENIENT = os.environ.get('LENIENT') == '1'
def local(p):
    for s in S:
        if p.startswith(s):
            l = p[len(s):]
            return l
    return None
def obj(o):
    if o.startswith('<'): return o[1:-1]
    if o.startswith('"'):
        m = re.match(r'^"(.*)"(?:@[\w-]+|\^\^<[^>]+>)?$', o, re.S)
        return (m.group(1) if m else o).encode().decode('unicode_escape','ignore') if '\\u' in o else (m.group(1) if m else o)
    return o
SL2 = {'co','com','net','org','gov','ac','edu','or','ne','go','gob','nic'}
def pld(url):
    h = (urlsplit(url).hostname or '').lower().rstrip('.')
    p = h.split('.')
    if len(p) >= 3 and (p[-2] in SL2 or len(p[-2]) <= 2) and len(p[-1]) == 2: return '.'.join(p[-3:])
    return '.'.join(p[-2:])
def pages(path):
    cur, buf, n_bad = None, [], 0
    with gzip.open(path, 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = Q.match(line)
            if not m: n_bad += 1; continue
            s, p, o, g = m.groups()
            if g != cur:
                if buf: yield cur, buf
                cur, buf = g, []
            buf.append((s, p, o))
    if buf: yield cur, buf
    sys.stderr.write(f'unparsed lines: {n_bad}\n')
def page_graph(trips):
    props = collections.defaultdict(lambda: collections.defaultdict(list))
    types = collections.defaultdict(set); md = set(); objs = set()
    for s, p, o in trips:
        if p != 'http://www.w3.org/1999/xhtml/microdata#item' and not o.startswith('"'): objs.add(o)
        if p == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
            t = local(o[1:-1]) if o.startswith('<') else None
            if t: types[s].add(t)
        elif p == 'http://www.w3.org/1999/xhtml/microdata#item':
            md.add(o)
        else:
            l = local(p)
            if l and LENIENT and l[:1].isupper() and not l[:2].isupper(): l = l[:1].lower() + l[1:]
            if l: props[s][l].append(o)
    return props, types, md, objs
def records(path):
    for g, trips in pages(path):
        props, types, md, objs = page_graph(trips)
        vparent = collections.defaultdict(list)
        for x, d in props.items():
            for v in d.get('hasVariant', []): vparent[v].append(x)
        for s, ts in types.items():
            if 'Product' not in ts: continue
            rec = {'g': g, 'pld': pld(g), 'md': s in md, 'nested': s in objs, 'p': {k: [obj(x) for x in v] for k, v in props[s].items()}, 'offers': []}
            def expand(node, depth=0):
                d = {k: [obj(x) for x in v] for k, v in props.get(node, {}).items()}
                if depth < 2:
                    for k in ('priceSpecification','shippingDetails','hasMerchantReturnPolicy','brand','shippingRate','deliveryTime'):
                        if k in props.get(node, {}):
                            d[k] = [expand(x, depth+1) if x in props else obj(x) for x in props[node][k]]
                d['_t'] = sorted(types.get(node, []))
                return d
            par = vparent.get(s, []) + [x for x in props[s].get('isVariantOf', []) if x in props]
            rec['parent'] = bool(par)
            for k in ('brand','hasMerchantReturnPolicy','gtin','gtin13','mpn'):
                if k not in props[s]:
                    for x in par:
                        if k in props.get(x, {}): props[s][k] = props[x][k]; break
            for k in ('brand','hasMerchantReturnPolicy'):
                if k in props[s]: rec['p'][k] = [expand(x) if x in props else obj(x) for x in props[s][k]]
            for o in props[s].get('offers', []):
                if o in props:
                    od = expand(o)
                    # AggregateOffer / nested offers
                    for sub in props.get(o, {}).get('offers', []):
                        if sub in props: rec['offers'].append(expand(sub))
                    rec['offers'].append(od)
            yield rec
