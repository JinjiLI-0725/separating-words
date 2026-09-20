#!/usr/bin/env python3
"""Audit saved exchange data and independently count the product language."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import time
import numpy as np
from analyze_v6_exchange import U,V,WU,WV,A,B,C,atomic_json
from analyze_v6_structure import read
from search_v6_product import run_word


def main():
    started=time.monotonic();prior={};prior_sets={}
    for name in ['v4_1_fast_scored_neighbors','v4_2_batch_local','v4_4_witness_guided','v4_5_beam']:
        d=json.loads(Path('results',name+'.json').read_text())
        rows=d.get('ranking',d.get('top',d.get('final_beam',[])))
        for r in rows:
            pair=r['u'],r['v'];score=r.get('separators',r.get('full_score'))
            if pair in prior:assert prior[pair]==score
            prior[pair]=score
            if 'witness_indices' in r:prior_sets[pair]=r['witness_indices']
    result={};allpairs=set()
    for name in ['v6_1_exchange','v6_2_exchange']:
        rows,M=read(Path('results',name));ix={(r['u'],r['v']):i for i,r in enumerate(rows)}
        old=M[ix[U,V]];assert old.sum()==52
        if (WU,WV) in ix:
            warm=M[ix[WU,WV]];assert warm.sum()==64 and not (old & warm).any()
        seenprior=0;reused=0
        for r,mask in zip(rows,M):
            pair=r['u'],r['v'];assert pair[0]!=pair[1] and len(pair[0])==len(pair[1])==47
            score=int(mask.sum());retained=int((mask & old).sum());new=score-retained
            assert r['score']==score and r['retained']==retained and r['introduced']==new
            assert r['eliminated']==52-retained and r['union']==52+new
            assert r['intersection']==retained and r['jaccard']==retained/(52+new)
            assert sum(r['by_k'])==score
            if pair in prior:assert score==prior[pair];seenprior+=1
            if pair in prior_sets:assert np.flatnonzero(mask).tolist()==prior_sets[pair]
            reused+=r['source']=='reused exact set'
            if name=='v6_2_exchange' and pair!=(U,V):assert pair not in allpairs and pair not in prior
        assert len(ix)==len(rows)
        result[name]=dict(rows=len(rows),best_score=min(r['score'] for r in rows),
            prior_scalar_score_matches=seenprior,reused_exact_sets=reused,newly_scored_pairs=len(rows)-seenprior)
        allpairs.update(ix)
    p=json.loads(Path('results/v6_2_product_candidates.json').read_text())
    tables=[p['transitions'][str(i)] for i in p['witness_ids']]
    start=tuple(x for t in tables for x in (run_word(t,A),0))
    # Independent forward recurrence; original code uses recursive suffix counts.
    states={(start,0):1}
    for ch in B:
        nxt=defaultdict(int)
        for (state,d),n in states.items():
            for bit in (0,1):
                target=tuple(tables[i//2][q][bit] for i,q in enumerate(state))
                nxt[target,d+(bit!=int(ch))]+=n
        states=nxt
    assert sum(states.values())==2**23
    histogram=[0]*24
    for (state,d),n in states.items():
        if all(state[2*i]==run_word(t,C,state[2*i+1]) for i,t in enumerate(tables)):
            histogram[d]+=n
    assert histogram==p['escape_counts_by_distance']
    equal_block='10'*11+'1';assert A+equal_block==equal_block+C
    result['independent_product_check']=dict(histogram=histogram,total=sum(histogram),nontrivial=sum(histogram)-1)
    result['elapsed_seconds']=time.monotonic()-started
    atomic_json(Path('results/v6_audit.json'),result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
