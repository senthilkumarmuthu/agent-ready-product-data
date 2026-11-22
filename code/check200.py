import json, random, sys, collections
sys.path.insert(0,'.')
from parse import pages, page_graph
from measure import score
recs=[json.loads(l) for l in open('recs_217.jsonl')]
fail=[r for r in recs if not score(r)['core']]
random.seed(20261120); samp=random.sample(fail,200); want=collections.defaultdict(list)
for r in samp: want[r['g']].append(r)
F={'price':('price','lowPrice'),'cur':('priceCurrency',),'av':('availability',),'id':('gtin','gtin8','gtin12','gtin13','gtin14','mpn')}
miss=collections.Counter(); linked=collections.Counter(); elsewhere=collections.Counter(); emptyid=0
for g,trips in pages(sys.argv[1]):
    if g not in want: continue
    props,types,md,objs=page_graph(trips)
    for r in want[g]:
        s=score(r)
        # which subject is this record? match by name+offers count
        cands=[x for x,t in types.items() if 'Product' in t and [o for o in props[x].get('name',[])][:1]==[('"'+r['p']['name'][0]+'"') if r['p'].get('name') else None][:1]]
        subj=cands[0] if cands else None
        reach=set()
        if subj:
            fr=[subj]+[x for x,d in props.items() if subj in d.get('hasVariant',[])]
            for d in range(3):
                nx=[]
                for x in fr:
                    if x in reach: continue
                    reach.add(x); nx+= [o for v in props.get(x,{}).values() for o in v if o in props]
                fr=nx
        allp=set(k for x in props for k in props[x]); rp=set(k for x in reach for k,v in props[x].items() if any(o.strip('"') for o in v))
        for m,ok in (('price',s['price_v']),('cur',s['cur_v']),('av',s['av_v']),('id',s['id_v'])):
            if ok: continue
            miss[m]+=1
            if any(f in rp for f in F[m]): linked[m]+=1
            elif any(f in allp for f in F[m]): elsewhere[m]+=1
print('failing fields in 200 records:',dict(miss)); print('value on a linked node (possible parser miss or invalid value):',dict(linked)); print('only on unrelated items:',dict(elsewhere))
