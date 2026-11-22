"""Export per-site aggregates for public release.

Reads the per-file aggregate JSONs, drops the probe reserve (raw records),
replaces each pay-level domain with a keyed pseudonym (HMAC-SHA256, key kept private,
same pseudonym for the same site in both releases), keeps the top-level domain,
and writes one gzipped CSV per release.

usage: python3 export_aggregates.py <agg_dir> <release> <out.csv.gz> <key_file>
"""
import sys, os, json, glob, gzip, hmac, hashlib, csv, collections

FIELDS = ['name_v', 'price', 'price_v', 'cur', 'cur_v', 'av', 'av_v', 'av_s', 'gtin', 'gtin_v', 'gtin_bad',
          'mpn_brand', 'id_v', 'brand', 'image', 'desc', 'sku', 'ship', 'ship_v', 'ret', 'ret_v', 'pvu', 'pvu_v',
          'offer_core', 'offer_core_s', 'core', 'core_gtin_only', 'core_av_strict', 'conflict']

agg_dir, release, out, key_file = sys.argv[1:5]
key = open(key_file, 'rb').read().strip()
rows = collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(os.path.join(agg_dir, '*.json'))):
    for k, c in json.load(open(f))['sites'].items():
        rows[k].update(c)
with gzip.open(out, 'wt', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['release', 'site_id', 'tld', 'format', 'position', 'n'] + FIELDS)
    for k in sorted(rows):
        pld, fmt, nest = k.split('\t')
        sid = hmac.new(key, pld.encode(), hashlib.sha256).hexdigest()[:16]
        c = rows[k]
        w.writerow([release, sid, pld.rsplit('.', 1)[-1], 'microdata' if fmt == 'md' else 'jsonld',
                    'nested' if nest == 'nest' else 'top', c['n']] + [c.get(x, 0) for x in FIELDS])
print(release, len(rows), 'rows')
