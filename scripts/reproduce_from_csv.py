"""Recompute the headline numbers from the released aggregate files.

usage: python3 scripts/reproduce_from_csv.py   (run from the repository root)
"""
import csv, gzip, collections


def load(path):
    sites = collections.defaultdict(lambda: collections.Counter())
    for r in csv.DictReader(gzip.open(path, 'rt')):
        s = sites[r['site_id']]
        for k, v in r.items():
            if k not in ('release', 'site_id', 'tld', 'format', 'position'):
                s[k] += int(v)
        s['jsonld_n' if r['format'] == 'jsonld' else 'micro_n'] += int(r['n'])
        s['jsonld_core' if r['format'] == 'jsonld' else 'micro_core'] += int(r['core'])
    return sites


def rate(sites, num, den='n', keys=None):
    keys = keys if keys is not None else sites.keys()
    return sum(sites[k][num] for k in keys) / sum(sites[k][den] for k in keys)


s24 = load('results/site_aggregates_2024-12.csv.gz')
s22 = load('results/site_aggregates_2022-12.csv.gz')
print(f"2024-12: {sum(s['n'] for s in s24.values()):,} records, {len(s24):,} sites")
print(f"2022-12: {sum(s['n'] for s in s22.values()):,} records")
print(f"H1  core-field rate 2024: {rate(s24, 'core'):.1%}")
print(f"H2  invalid share of GTINs 2024: {rate(s24, 'gtin_bad', 'gtin'):.1%}")
print(f"H3b JSON-LD {rate(s24, 'jsonld_core', 'jsonld_n'):.1%} vs Microdata {rate(s24, 'micro_core', 'micro_n'):.1%}")
print(f"H4  core-field rate 2022 {rate(s22, 'core'):.1%} -> 2024 {rate(s24, 'core'):.1%}")
both = set(s24) & set(s22)
print(f"    sites in both releases: {len(both):,}; {rate(s22, 'core', keys=both):.1%} -> {rate(s24, 'core', keys=both):.1%}")
size = {k: s['n'] for k, s in s24.items()}
big = [s['core'] / s['n'] for k, s in s24.items() if size[k] > 1000]
small = [s['core'] / s['n'] for k, s in s24.items() if 2 <= size[k] <= 10]
print(f"H3  mean site core-field rate: >1,000 records {sum(big) / len(big):.1%}, 2-10 records {sum(small) / len(small):.1%}")
print("Intervals come from code/boot.py and code/analyze2.py; see results/hypothesis_results.json.")
