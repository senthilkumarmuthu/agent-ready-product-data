import sys, json, re, collections
ISO = set("""AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD CAD CDF CHF CLP CNY COP CRC CUC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SLL SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD UYU UZS VES VED VND VUV WST XAF XCD XOF XPF YER ZAR ZMW ZWL ZWG XCG""".split())
AVAIL = {a.lower(): a for a in "InStock OutOfStock PreOrder BackOrder Discontinued InStoreOnly LimitedAvailability OnlineOnly PreSale SoldOut Reserved MadeToOrder".split()}
PLACEHOLDER = {'', 'product', 'untitled', 'n/a', 'na', 'null', 'none', 'undefined', 'test', 'name', 'product name', 'title'}
def first(v):
    for x in v or []:
        if isinstance(x, str) and x.strip(): return x.strip()
    return None
def num(s):
    if s is None: return None
    if re.fullmatch(r'\s*\d+(\.\d+)?[eE][+-]?\d+\s*', s):
        x = float(s)
        return x if x > 0 else None
    t = re.sub(r'[^\d.,\-]', '', s)
    if not t or t.startswith('-'): return None
    if ',' in t and '.' in t:
        t = t.replace(',', '') if t.rfind('.') > t.rfind(',') else t.replace('.', '').replace(',', '.')
    elif ',' in t:
        t = t.replace(',', '.') if re.search(r',\d{1,2}$', t) else t.replace(',', '')
    try: x = float(t)
    except ValueError: return None
    return x if x > 0 else None
def avail(s, strict=False):
    if not s: return None
    t = s.strip()
    if strict:
        m = re.match(r'^https?://schema\.org/(\w+)$', t)
        return AVAIL.get(m.group(1).lower()) if m else None
    t = re.sub(r'^https?://(www\.)?schema\.org/', '', t, flags=re.I).strip().replace(' ', '')
    return AVAIL.get(t.lower())
def gtin_ok(g):
    d = re.sub(r'[\s\-]', '', g or '')
    if not d.isdigit() or len(d) not in (8, 12, 13, 14): return False
    body, chk = d[:-1], int(d[-1])
    s = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
    return (10 - s % 10) % 10 == chk
GT = ('gtin', 'gtin8', 'gtin12', 'gtin13', 'gtin14')
def brand_name(v):
    for x in v or []:
        if isinstance(x, dict):
            n = first(x.get('name'))
            if n: return n
        elif isinstance(x, str) and x.strip() and not x.startswith('_:'): return x.strip()
    return None
def score(r, crawl='2024-12'):
    p = r['p']; offers = r['offers']
    def get(k):
        v = first(p.get(k))
        if v: return v
        for o in offers:
            v = first(o.get(k))
            if v: return v
        return None
    out = {}
    nm = first(p.get('name'))
    out['name'] = nm is not None
    out['name_v'] = bool(nm) and nm.lower() not in PLACEHOLDER and not re.match(r'^https?://', nm) and '{{' not in nm
    prices = []; best = dict(price=False, cur=False, cur_v=False, av=False, av_v=False, av_s=False, price_v=False, offer_core=False, offer_core_s=False)
    for o in offers:
        pr = first(o.get('price')) or first(o.get('lowPrice'))
        if not pr:
            for ps in o.get('priceSpecification', []):
                if isinstance(ps, dict):
                    pr = first(ps.get('price'))
                    if pr: break
        cu = first(o.get('priceCurrency'))
        if not cu:
            for ps in o.get('priceSpecification', []):
                if isinstance(ps, dict) and first(ps.get('priceCurrency')): cu = first(ps.get('priceCurrency')); break
        av = first(o.get('availability'))
        pv = num(pr); cv = bool(cu) and cu.strip().upper() in ISO and cu.strip() == cu.strip().upper(); avv = avail(av) is not None
        best['price'] |= pr is not None; best['price_v'] |= pv is not None
        best['cur'] |= cu is not None; best['cur_v'] |= cv
        best['av'] |= av is not None; best['av_v'] |= avv; best['av_s'] |= avail(av, True) is not None
        best['offer_core'] |= (pv is not None and cv and avv)
        best['offer_core_s'] |= (pv is not None and cv and avail(av, True) is not None)
        prices.append((pv, first(o.get('sku')) or first(p.get('sku')), avail(av)))
    out.update(best)
    gt = [first(p.get(k)) or next((first(o.get(k)) for o in offers if first(o.get(k))), None) for k in GT]
    gt = [g for g in gt if g]
    out['gtin'] = bool(gt); out['gtin_v'] = any(gtin_ok(g) for g in gt); out['gtin_bad'] = bool(gt) and not out['gtin_v']
    mpn = get('mpn'); br = brand_name(p.get('brand'))
    out['mpn_brand'] = bool(mpn) and bool(br)
    out['id_v'] = out['gtin_v'] or out['mpn_brand']
    out['brand'] = br is not None; out['image'] = get('image') is not None; out['desc'] = get('description') is not None; out['sku'] = get('sku') is not None
    sh = [x for o in offers for x in o.get('shippingDetails', [])]
    out['ship'] = bool(sh)
    out['ship_v'] = any(isinstance(x, dict) and (x.get('shippingRate') or x.get('deliveryTime')) for x in sh)
    rp = [x for o in offers for x in o.get('hasMerchantReturnPolicy', [])] + list(p.get('hasMerchantReturnPolicy', []))
    out['ret'] = bool(rp)
    out['ret_v'] = any(isinstance(x, dict) and (x.get('merchantReturnDays') or x.get('returnPolicyCategory')) for x in rp)
    pvu = get('priceValidUntil'); out['pvu'] = pvu is not None
    out['pvu_v'] = bool(pvu) and re.match(r'^\d{4}-\d{2}', pvu) is not None and pvu[:7] >= crawl
    out['core'] = out['offer_core'] and out['id_v']
    out['core_gtin_only'] = out['offer_core'] and out['gtin_v']
    out['core_av_strict'] = out['offer_core_s'] and out['id_v']
    out['n_offers'] = len(offers)
    # conflict within record: same sku, different valid prices, distinct availability not required
    by = collections.defaultdict(set)
    for pv, sku, _ in prices:
        if pv: by[sku].add(round(pv, 2))
    out['conflict'] = any(len(v) > 1 for v in by.values()) and len(offers) > 1
    return out
if __name__ == '__main__':
    crawl = sys.argv[2] if len(sys.argv) > 2 else '2024-12'
    tot = collections.Counter(); n = 0; site = collections.defaultdict(lambda: [0, 0]); fails = []
    for line in open(sys.argv[1]):
        r = json.loads(line); s = score(r, crawl); n += 1
        for k, v in s.items():
            if isinstance(v, bool): tot[k] += v
        site[r['pld']][0] += 1; site[r['pld']][1] += s['core']
    print('records', n, 'sites', len(site))
    for k in sorted(tot): print(f'{k:16s} {tot[k]/n:7.3%}')
    rates = [c / t for t, c in site.values()]
    print('site-mean core', sum(rates) / len(rates), 'site readiness(>=90%)', sum(r >= .9 for r in rates) / len(rates))
