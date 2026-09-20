#!/usr/bin/env python3
"""Analyze finite exchange certificates and the champion/warm mutation square."""
import argparse
from collections import Counter, defaultdict
import json
import time
import zipfile
from pathlib import Path
import numpy as np
from analyze_v6_exchange import N,U,V,A,B,C,atomic_json,flip_many


def read(prefix):
    # A concurrent producer may be finishing an append-only checkpoint.
    for attempt in range(20):
        try:
            text=prefix.with_suffix('.jsonl').read_text()
            rows=[json.loads(s) for s in text.splitlines()]
            with np.load(prefix.with_suffix('.sets.npz')) as archive:
                masks=np.unpackbits(archive['packed'],axis=1,count=N).astype(bool)
            if prefix.with_suffix('.jsonl').read_text()==text and len(masks)>=len(rows):
                return rows,masks[:len(rows)]
        except (EOFError,zipfile.BadZipFile,OSError,ValueError):
            pass
        time.sleep(0.25)
    raise RuntimeError('could not read a consistent exchange checkpoint')



def cover(masks):
    """Greedy upper bound and exact 1/2-witness test on finite candidates."""
    active=np.flatnonzero(masks.any(axis=0)); sig={}
    for w in active:
        bits=int.from_bytes(np.packbits(masks[:,w],bitorder='little').tobytes(),'little')
        sig.setdefault(bits,int(w))
    full=(1<<len(masks))-1
    uncovered=full;chosen=[]
    while uncovered:
        bits=max(sig,key=lambda b:(b&uncovered).bit_count())
        if not bits&uncovered: break
        chosen.append(sig[bits]);uncovered &= ~bits
    minimum=1 if full in sig else None
    exact=[sig[full]] if minimum else None
    # Compress redundant columns by inclusion; equal columns already merged.
    maximal=[]
    for bits in sorted(sig,key=int.bit_count,reverse=True):
        if not any(bits & ~sup==0 for sup in maximal): maximal.append(bits)
    if minimum is None:
        for i,a in enumerate(maximal):
            for b in maximal[i+1:]:
                if a|b==full:
                    minimum=2;exact=[sig[a],sig[b]];break
            if minimum: break
    return dict(greedy_witness_ids=chosen,greedy_size=len(chosen),uncovered=uncovered.bit_count(),
        exact_minimum=minimum,exact_witness_ids=exact,lower_bound=minimum or 3,
        distinct_incidence_columns=len(sig),maximal_columns=len(maximal))


def analyze(prefix):
    rows,M=read(prefix); lookup={(r['u'],r['v']):i for i,r in enumerate(rows)}
    old=M[lookup[U,V]]
    low=[i for i,r in enumerate(rows) if r['score']<=200]
    zero=[i for i in low if rows[i]['retained']==0]
    result={'low_score_threshold':200,'low_score_count':len(low),'low_score_cover':cover(M[low]),
        'low_zero_old_count':len(zero),
        'low_zero_old_common_witnesses':np.flatnonzero(M[zero].all(axis=0)).tolist() if zero else []}
    corners=[]
    for pos in ([],[5],[10],[5,10]):
        b=flip_many(B,pos);i=lookup.get((A+b,b+C))
        if i is not None: corners.append(i)
    if len(corners)==4:
        cells=defaultdict(list)
        for w in np.flatnonzero(M[corners].any(axis=0)):
            cells[''.join(str(int(x)) for x in M[corners,w])].append(int(w))
        result['square']={'corner_candidates':corners,'positions':[[],[5],[10],[5,10]],
            'scores':[rows[i]['score'] for i in corners],
            'cells':dict(cells),'cell_sizes':{s:len(ids) for s,ids in cells.items()},
            'edges':[dict(source=a,target=b,eliminated=int((M[a]&~M[b]).sum()),introduced=int((M[b]&~M[a]).sum()))
                     for a,b in [(corners[0],corners[1]),(corners[0],corners[2]),(corners[1],corners[3]),(corners[2],corners[3])]]}
    # Pareto frontier maximizing eliminated old witnesses, minimizing replacements.
    pairs=sorted(set((r['eliminated'],r['introduced']) for r in rows))
    result['pareto']=[dict(eliminated=e,introduced=n,candidates=[r['id'] for r in rows if (r['eliminated'],r['introduced'])==(e,n)])
        for e,n in pairs if not any(e1>=e and n1<=n and (e1,n1)!=(e,n) for e1,n1 in pairs)]
    # Identify shared-block positions recurring among best nontrivial exchanges.
    positions=Counter()
    for r in sorted(rows,key=lambda r:(r['score'],r['introduced'])):
        aligned=[m for m in r['mutations'] if m['type']=='aligned24']
        if aligned and len(aligned[0]['positions'])==2 and r['score']<=120:
            positions.update(aligned[0]['positions'])
    result['position_frequency_score_le120']=dict(positions)
    pool_path=Path('results/v6_permutation_pool.json')
    if pool_path.exists():
        from search_v4_4_witness_guided import endpoint_matrix
        aligned=[i for i,r in enumerate(rows) if r['u'][:24]==A and r['v'][23:]==C and r['u'][24:]==r['v'][:23]]
        words=sorted({w for i in aligned for w in (rows[i]['u'],rows[i]['v'])})
        wi={w:i for i,w in enumerate(words)}
        pool=np.asarray(json.loads(pool_path.read_text())['transitions'],dtype=np.uint8)
        E=endpoint_matrix(pool,words)
        branch=[]
        for i in aligned:
            r=rows[i];permutation=int(np.count_nonzero(E[wi[r['u']]]!=E[wi[r['v']]]))
            assert permutation<=r['score']
            if (r['u'],r['v'])==(U,V): assert permutation==0
            if r['score']==64 and r['mutations'][0]['type']=='warm64': assert permutation==64
            branch.append(dict(candidate=i,score=r['score'],permutation=permutation,singular=r['score']-permutation))
        result['aligned_branch_counts']=branch
        result['aligned_low_zero_singular']=[r for r in branch if r['score']<=200 and r['singular']==0]
        result['aligned_low_zero_permutation']=[r for r in branch if r['score']<=200 and r['permutation']==0]
    atomic_json(prefix.with_suffix('.structure.json'),result)
    print(json.dumps(result,indent=2))



if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('prefix',type=Path)
    args=p.parse_args();analyze(args.prefix)
