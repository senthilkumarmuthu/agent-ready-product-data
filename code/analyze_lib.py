import json, glob, collections, numpy as np, sys
B = 1000; SEED = 20261120
F = ['name_v','price_v','cur_v','av_v','av_s','gtin','gtin_v','gtin_bad','mpn_brand','id_v','brand','image','desc','sku','ship','ship_v','ret','ret_v','pvu','pvu_v','offer_core','core','core_gtin_only','core_av_strict','conflict']
def load(d, top_only=False):
    S = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))  # pld -> fmt -> counts
    for f in sorted(glob.glob(d + '/*.json')):
        for k, c in json.load(open(f))['sites'].items():
            p, fmt, nest = k.split('\t')
            if top_only and nest == 'nest': continue
            S[p][fmt].update(c)
    pl = sorted(S)
    A = {fmt: {k: np.array([S[p][fmt].get(k, 0) for p in pl], float) for k in F + ['n']} for fmt in ('jl', 'md')}
    T = {k: A['jl'][k] + A['md'][k] for k in F + ['n']}
    return pl, T, A
def weights(n_sites, rng, chunk):
    for _ in range(B // chunk):
        yield rng.multinomial(n_sites, np.full(n_sites, 1 / n_sites), size=chunk).astype(np.float32)
def boot_ratio(num, den, rng, extra=None):
    """record-level ratio sum(num)/sum(den), bootstrap over sites; returns (est, lo, hi, draws)"""
    n = len(den); chunk = max(1, min(100, int(2e7 // n)))
    draws = []
    for W in weights(n, rng, chunk):
        draws.append((W @ num) / (W @ den))
    d = np.concatenate(draws); est = num.sum() / den.sum()
    return est, np.percentile(d, 2.5), np.percentile(d, 97.5), d
def ci(d): return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))

import os, pickle
_load = load
def load(d, top_only=False):
    fn = f'cache_{d}{"_top" if top_only else ""}.pkl'
    if os.path.exists(fn): return pickle.load(open(fn, 'rb'))
    r = _load(d, top_only); pickle.dump(r, open(fn, 'wb')); return r
