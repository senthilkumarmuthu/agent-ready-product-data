import json, collections, numpy as np
from analyze_lib import load, F
rng = np.random.default_rng(20261120); B = 1000
I = {k: i for i, k in enumerate(F)}; N, JC, JN, MC, MN = 25, 26, 27, 28, 29
R24, R22, R24t = np.load('boot_a24.npy').astype(float), np.load('boot_a22.npy').astype(float), np.load('boot_a24_top.npy').astype(float)
pl24, T24, A24 = load('a24'); pl22, T22, A22 = load('a22')
def pct(d): return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]
def rate(T, k, den='n'): return float(T[k].sum() / T[den].sum())
out = {'sample': {'2024_records': int(T24['n'].sum()), '2024_sites': len(pl24), '2022_records': int(T22['n'].sum()), '2022_sites': len(pl22),
                  'microdata_share_2024': rate(A24['md'], 'n') if False else float(A24['md']['n'].sum() / T24['n'].sum())}}
out['fields'] = {k: {'2024': [rate(T24, k)] + pct(R24[:, I[k]] / R24[:, N]), '2022': [rate(T22, k)] + pct(R22[:, I[k]] / R22[:, N])} for k in F if k != 'gtin_bad'}
c24 = R24[:, I['core']] / R24[:, N]; c22 = R22[:, I['core']] / R22[:, N]
e = rate(T24, 'core'); out['H1'] = {'est': e, 'ci': pct(c24), 'supported': bool(e < .5 and pct(c24)[1] < .5)}
d = R24[:, I['gtin_bad']] / R24[:, I['gtin']]; e = rate(T24, 'gtin_bad', 'gtin')
out['H2'] = {'est': e, 'ci': pct(d), 'supported': bool(e >= .05 and pct(d)[0] > .05), '2022': [rate(T22, 'gtin_bad', 'gtin')] + pct(R22[:, I['gtin_bad']] / R22[:, I['gtin']])}
sr = T24['core'] / T24['n']; n = T24['n']
band = np.select([n == 1, n <= 10, n <= 100, n <= 1000], [0, 1, 2, 3], 4); names = ['1', '2-10', '11-100', '101-1000', '>1000']
out['site'] = {'mean_site_core': float(sr.mean()), 'readiness_90': float((sr >= .9).mean()), 'sites_with_zero_core': float((sr == 0).mean())}
out['bands'] = {}
for b in range(5):
    m = band == b; x = sr[m]
    bm = [rng.choice(x, len(x)).mean() for _ in range(B)]
    out['bands'][names[b]] = {'sites': int(m.sum()), 'records': int(n[m].sum()), 'site_mean_core': [float(x.mean())] + pct(bm), 'record_core': float(T24['core'][m].sum() / n[m].sum())}
hi_, lo_ = sr[band == 4], sr[band == 1]
dd = [rng.choice(hi_, len(hi_)).mean() - rng.choice(lo_, len(lo_)).mean() for _ in range(B)]; e = float(hi_.mean() - lo_.mean())
out['H3'] = {'est': e, 'ci': pct(dd), 'supported': bool(e >= .10 and pct(dd)[0] > 0)}
dj = R24[:, JC] / R24[:, JN]; dm = R24[:, MC] / R24[:, MN]
ej, em = rate(A24['jl'], 'core'), rate(A24['md'], 'core')
out['H3b'] = {'est': ej - em, 'jsonld': ej, 'microdata': em, 'ci': pct(dj - dm), 'supported': bool(ej - em >= .05 and pct(dj - dm)[0] > 0),
              '2022_jsonld': rate(A22['jl'], 'core'), '2022_microdata': rate(A22['md'], 'core')}
e = rate(T24, 'core') - rate(T22, 'core')
out['H4'] = {'est': e, 'r2024': rate(T24, 'core'), 'r2022': rate(T22, 'core'), 'ci': pct(c24 - c22), 'supported': bool(e > 0 and pct(c24 - c22)[0] > 0)}
both = sorted(set(pl24) & set(pl22)); i24 = {p: i for i, p in enumerate(pl24)}; i22 = {p: i for i, p in enumerate(pl22)}
a = np.array([i24[p] for p in both]); b_ = np.array([i22[p] for p in both])
M = np.stack([T24['core'][a], T24['n'][a], T22['core'][b_], T22['n'][b_]], 1)
W = rng.poisson(1.0, size=(B, len(both))); S = W @ M
out['H4_both'] = {'sites': len(both), 'r2024': float(M[:, 0].sum() / M[:, 1].sum()), 'r2022': float(M[:, 2].sum() / M[:, 3].sum()), 'ci_diff': pct(S[:, 0] / S[:, 1] - S[:, 2] / S[:, 3])}
out['H4_both']['est'] = out['H4_both']['r2024'] - out['H4_both']['r2022']
_, Tt, _ = load('a24', top_only=True)
w = np.where(n > 1000, .1, 1.); Wd = rng.poisson(1.0, size=(B, len(n)))
out['sensitivity'] = {
 'core_av_strict': [rate(T24, 'core_av_strict')] + pct(R24[:, I['core_av_strict']] / R24[:, N]),
 'core_gtin_only': [rate(T24, 'core_gtin_only')] + pct(R24[:, I['core_gtin_only']] / R24[:, N]),
 'top_level_only': [rate(Tt, 'core')] + pct(R24t[:, I['core']] / R24t[:, N]),
 'largest_downweighted': [float((T24['core'] * w).sum() / (n * w).sum())] + pct((Wd @ (T24['core'] * w)) / (Wd @ (n * w)))}
tld = np.array([p.rsplit('.', 1)[-1] for p in pl24]); out['tld'] = {}
for t, _ in collections.Counter(tld).most_common(8):
    m = tld == t; out['tld'][t] = {'sites': int(m.sum()), 'records': int(n[m].sum()), 'core': float(T24['core'][m].sum() / n[m].sum())}
json.dump(out, open('results.json', 'w'), indent=1)
for k in ('sample', 'H1', 'H2', 'H3', 'H3b', 'H4', 'H4_both', 'site', 'bands', 'sensitivity', 'tld'): print(k, json.dumps(out[k]))
