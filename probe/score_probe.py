import json, re, math, random, collections, sys
T = json.load(open('probe_truth.json'))
items = {json.loads(l)['id']: json.loads(l) for l in open('probe_items.jsonl')}
def norm(s): return re.sub(r'[\s\-]', '', str(s)).lower()
def cp(k, n, a=.05):
    def cdf(k, n, p): return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k+1))
    def solve(f, lo=0., hi=1.):
        for _ in range(60):
            m = (lo+hi)/2
            if f(m): hi = m
            else: lo = m
        return (lo+hi)/2
    lo = 0. if k == 0 else solve(lambda p: 1-cdf(k-1, n, p) >= a/2)
    hi = 1. if k == n else solve(lambda p: cdf(k, n, p) <= a/2)
    return lo, hi
def judge(it, raw):
    try: a = json.loads(raw)
    except Exception: return False, 'unparseable'
    t = T[it['rec']]; cond, q = it['cond'], it['q']
    missing = (cond == 'c2_no_price' and q == 'price') or (cond == 'c3_no_availability' and q == 'stock') or (cond == 'c4_no_identifier' and q == 'id') or cond.startswith('c5')
    if q == 'price':
        p, c = a.get('price'), a.get('currency')
        if missing: return p is None, ('abstained' if p is None else 'invented')
        if p is None: return False, 'abstained'
        try: ok = any(abs(float(p) - tp) < 0.01 and str(c or '').strip().upper() == tc for tp, tc in t['prices'])
        except Exception: ok = False
        return ok, 'answered'
    if q == 'stock':
        s = a.get('in_stock_today')
        if missing: return s is None, ('abstained' if s is None else 'invented')
        if s is None: return False, 'abstained'
        return s in t['stock'], 'answered'
    g, m = a.get('gtin'), a.get('mpn')
    if missing: return g is None and m is None, ('abstained' if g is None and m is None else 'invented')
    if g is None and m is None: return False, 'abstained'
    return any(x is not None and norm(x) in t['ids'] for x in (g, m)), 'answered'
out = {}
for model in ('llama3.2_3b', 'qwen2.5_3b'):
    R = {}; kinds = collections.Counter()
    for l in open(f'answers_{model}.jsonl'):
        x = json.loads(l); it = items[x['id']]; ok, kind = judge(it, x['raw'])
        R[(it['rec'], it['cond'], it['q'])] = ok; kinds[(it['cond'], it['q'], kind)] += 1
    acc = {}
    for (rec, cond, q), ok in R.items(): acc.setdefault((cond, q), []).append((rec, ok))
    res = {}
    for (cond, q), v in sorted(acc.items()):
        k = sum(o for _, o in v); n = len(v); lo, hi = cp(k, n)
        res[f'{cond}|{q}'] = {'acc': k/n, 'ci': [lo, hi], 'n': n, 'kinds': {kd: c for (cc, qq, kd), c in kinds.items() if cc == cond and qq == q}}
    drops = {}
    rng = random.Random(20261120)
    for q, cx in (('price', 'c2_no_price'), ('stock', 'c3_no_availability'), ('id', 'c4_no_identifier')):
        base = dict(acc[('c1_complete', q)]); rem = dict(acc[(cx, q)]); recs = sorted(set(base) & set(rem))
        d = [base[r] - rem[r] for r in recs]; est = sum(d)/len(d)
        bs = sorted(sum(rng.choice(d) for _ in d)/len(d) for _ in range(2000))
        drops[q] = {'drop': est, 'ci': [bs[49], bs[1949]], 'complete': sum(base.values())/len(base), 'removed': sum(rem.values())/len(rem)}
    out[model] = {'conditions': res, 'drops': drops, 'unparseable': sum(c for (cc, qq, kd), c in kinds.items() if kd == 'unparseable')}
out['H5_supported'] = all(out[m]['drops'][q]['drop'] >= .20 for m in ('llama3.2_3b', 'qwen2.5_3b') for q in ('price', 'stock', 'id'))
json.dump(out, open('probe_results.json', 'w'), indent=1)
for m in ('llama3.2_3b', 'qwen2.5_3b'):
    print('==', m, 'unparseable', out[m]['unparseable'])
    for k, v in out[m]['conditions'].items(): print(f"{k:38s} {v['acc']:6.1%} [{v['ci'][0]:.1%},{v['ci'][1]:.1%}] n={v['n']} {v['kinds']}")
    for q, v in out[m]['drops'].items(): print(f"  DROP {q:6s} complete {v['complete']:.1%} removed {v['removed']:.1%} drop {v['drop']*100:+.1f} pts [{v['ci'][0]*100:+.1f},{v['ci'][1]*100:+.1f}]")
print('H5 supported:', out['H5_supported'])
