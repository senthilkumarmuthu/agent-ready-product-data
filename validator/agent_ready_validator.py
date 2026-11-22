#!/usr/bin/env python3
"""Agent-ready product data validator.

Checks schema.org Product markup (JSON-LD) against the agent-ready product data
profile: a core tier (cost, stock, identity), a transaction tier (shipping, returns,
price date) and a comparison tier (brand, image, description). Each rule is tied to
a failure measured in "Can Machines Read the Store?" (Muthu, 2026).

Standard library only.

usage:
  python3 agent_ready_validator.py page.html        # reads every <script type="application/ld+json">
  python3 agent_ready_validator.py product.jsonld   # a JSON-LD file
  python3 agent_ready_validator.py page.html --json # machine-readable output
"""
import sys, re, json, datetime

ISO4217 = set("""AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD
CAD CDF CHF CLP CNY COP CRC CUC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD
HKD HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD
MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON
RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SLL SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH
UGX USD UYU UZS VES VED VND VUV WST XAF XCD XCG XOF XPF YER ZAR ZMW ZWG ZWL""".split())
AVAILABILITY = {"InStock", "OutOfStock", "PreOrder", "BackOrder", "Discontinued", "InStoreOnly", "LimitedAvailability",
                "OnlineOnly", "PreSale", "SoldOut", "Reserved", "MadeToOrder"}
GTIN_KEYS = ("gtin", "gtin8", "gtin12", "gtin13", "gtin14")
KNOWN = {"offers", "price", "priceCurrency", "availability", "priceSpecification", "brand", "name", "image",
         "description", "sku", "mpn", "shippingDetails", "hasMerchantReturnPolicy", "priceValidUntil",
         "lowPrice", "hasVariant", "isVariantOf"} | set(GTIN_KEYS)


def as_list(v):
    return v if isinstance(v, list) else ([] if v is None else [v])


def first(v):
    for x in as_list(v):
        if isinstance(x, (str, int, float)) and str(x).strip():
            return str(x).strip()
        if isinstance(x, dict) and x.get("@value") is not None:
            return str(x["@value"]).strip()
    return None


def num(s):
    if s is None:
        return None
    s = s.strip()
    try:
        x = float(s) if re.fullmatch(r"\d+(\.\d+)?([eE][+-]?\d+)?", s) else None
    except ValueError:
        x = None
    if x is None:
        t = re.sub(r"[^\d.,]", "", s)
        if "," in t and "." in t:
            t = t.replace(",", "") if t.rfind(".") > t.rfind(",") else t.replace(".", "").replace(",", ".")
        elif "," in t:
            t = t.replace(",", ".") if re.search(r",\d{1,2}$", t) else t.replace(",", "")
        try:
            x = float(t)
        except ValueError:
            return None
    return x if x > 0 else None


def gtin_ok(g):
    d = re.sub(r"[\s-]", "", g or "")
    if not d.isdigit() or len(d) not in (8, 12, 13, 14):
        return False
    s = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(d[:-1])))
    return (10 - s % 10) % 10 == int(d[-1])


def types(node):
    return {str(t).rsplit("/", 1)[-1] for t in as_list(node.get("@type"))}


def walk(node, out):
    if isinstance(node, dict):
        if "Product" in types(node):
            out.append(node)
        for v in node.values():
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


def case_errors(node, path=""):
    errs = []
    if isinstance(node, dict):
        lower = {k.lower(): k for k in KNOWN}
        for k, v in node.items():
            if not k.startswith("@") and k not in KNOWN and k.lower() in lower:
                errs.append(f"{path}{k} should be {lower[k.lower()]}")
            errs += case_errors(v, f"{path}{k}.")
    elif isinstance(node, list):
        for v in node:
            errs += case_errors(v, path)
    return errs


def check(product, today=None):
    today = today or datetime.date.today()
    offers = []
    for o in as_list(product.get("offers")):
        if isinstance(o, dict):
            offers += [x for x in as_list(o.get("offers")) if isinstance(x, dict)]
            offers.append(o)
    res = {"name": first(product.get("name")), "core": [], "transaction": [], "comparison": []}

    def rule(tier, ok, text):
        res[tier].append({"pass": bool(ok), "rule": text})

    good_offer = False
    for o in offers:
        pr = first(o.get("price")) or first(o.get("lowPrice"))
        cu = first(o.get("priceCurrency"))
        for ps in as_list(o.get("priceSpecification")):
            if isinstance(ps, dict):
                pr = pr or first(ps.get("price"))
                cu = cu or first(ps.get("priceCurrency"))
        av = first(o.get("availability")) or ""
        m = re.fullmatch(r"https?://schema\.org/(\w+)", av)
        if num(pr) and cu in ISO4217 and m and m.group(1) in AVAILABILITY:
            good_offer = True
    rule("core", good_offer, "An Offer has a positive price, an ISO 4217 priceCurrency and a full schema.org availability URL")

    gt = [first(product.get(k)) or next((first(o.get(k)) for o in offers if first(o.get(k))), None) for k in GTIN_KEYS]
    gt = [g for g in gt if g]
    mpn = first(product.get("mpn")) or next((first(o.get("mpn")) for o in offers if first(o.get("mpn"))), None)
    brand = product.get("brand")
    brand_name = first(brand.get("name")) if isinstance(brand, dict) else first(brand)
    bad = [g for g in gt if not gtin_ok(g)]
    rule("core", any(gtin_ok(g) for g in gt) or (mpn and brand_name),
         "The Product has a GTIN with a valid GS1 check digit, or an MPN together with a brand"
         + (f" (invalid GTIN: {', '.join(bad)})" if bad else ""))

    by_sku = {}
    for o in offers:
        sku = first(o.get("sku")) or first(product.get("sku"))
        if sku is None or o.get("priceSpecification"):
            continue
        by_sku.setdefault(sku, set()).add((num(first(o.get("price"))), first(o.get("availability"))))
    conflicts = [s for s, v in by_sku.items() if len(v) > 1]
    rule("core", not conflicts, "No SKU appears in two offers with different price or availability"
         + (f" (conflicting SKU: {', '.join(conflicts)})" if conflicts else ""))

    ce = case_errors(product)
    rule("core", not ce, "Property names use schema.org's exact case" + (f" ({'; '.join(ce[:3])})" if ce else ""))

    ship = [s for o in offers for s in as_list(o.get("shippingDetails")) if isinstance(s, dict)]
    rule("transaction", any(s.get("shippingRate") or s.get("deliveryTime") for s in ship),
         "An Offer has shippingDetails with a rate or a delivery time")
    rp = [r for o in offers for r in as_list(o.get("hasMerchantReturnPolicy"))] + as_list(product.get("hasMerchantReturnPolicy"))
    rule("transaction", any(isinstance(r, dict) and (r.get("merchantReturnDays") or r.get("returnPolicyCategory")) for r in rp),
         "The return policy is defined on the record, with a return window or a policy category")
    pvu = next((first(o.get("priceValidUntil")) for o in offers if first(o.get("priceValidUntil"))), None)
    rule("transaction", pvu is None or pvu[:10] >= today.isoformat(), "priceValidUntil, when present, is not in the past")

    rule("comparison", brand_name, "The Product has a brand")
    rule("comparison", first(product.get("image")) or isinstance(product.get("image"), dict), "The Product has an image")
    rule("comparison", first(product.get("description")), "The Product has a description")
    for tier in ("core", "transaction", "comparison"):
        res[tier + "_pass"] = all(r["pass"] for r in res[tier])
    return res


def load(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    blocks = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.S | re.I)
    docs = []
    for b in (blocks or [text]):
        try:
            docs.append(json.loads(b))
        except json.JSONDecodeError as e:
            print(f"warning: skipped a JSON-LD block that doesn't parse ({e})", file=sys.stderr)
    return docs


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    products = []
    for d in load(sys.argv[1]):
        walk(d, products)
    if not products:
        sys.exit("No schema.org Product found.")
    results = [check(p) for p in products]
    if "--json" in sys.argv:
        print(json.dumps(results, indent=2))
        return
    for r in results:
        print(f"\nProduct: {r['name']}")
        for tier in ("core", "transaction", "comparison"):
            print(f"  {tier.capitalize()} tier: {'PASS' if r[tier + '_pass'] else 'FAIL'}")
            for x in r[tier]:
                print(f"    [{'ok' if x['pass'] else '--'}] {x['rule']}")


if __name__ == "__main__":
    main()
