#!/usr/bin/env python3
"""Check the elementary 12th-power lemma and profile W0/W64 projections."""
from collections import Counter
import itertools
import json
from pathlib import Path
import time
from separating_words.canonical_generator import generate_canonical_dfas
from analyze_v6_exchange import U,V,WU,WV,atomic_json


def power(f,n):
    out=tuple(range(len(f)))
    for _ in range(n):out=tuple(f[q] for q in out)
    return out


def is_full_five_cycle(f):
    if len(f)!=5:return False
    q=0;seen=set()
    while q not in seen:
        seen.add(q);q=f[q]
    return len(seen)==5 and q==0


def check_lemma():
    counts={}
    for k in range(1,6):
        checked=exceptions=0
        for f in itertools.product(range(k),repeat=k):
            exception=power(f,12)!=power(f,24)
            assert exception==is_full_five_cycle(f)
            checked+=1;exceptions+=exception
        counts[k]=dict(maps=checked,non_idempotent_12th_powers=exceptions)
    return counts


def main():
    started=time.monotonic()
    prior=json.loads(Path('results/v4_5_beam.json').read_text())
    bypair={(r['u'],r['v']):r['witness_indices'] for r in prior['final_beam']}
    ids=set(bypair[U,V]) | set(bypair[WU,WV])
    profiles={};idx=0
    for k in range(1,6):
        for t in generate_canonical_dfas(k):
            if idx in ids:
                # Applying symbol 1 then 0 corresponds to the block '10'.
                f=tuple(t[t[q][1]][0] for q in range(k))
                g=tuple(t[t[q][0]][1] for q in range(k))
                fp,gp=power(f,12),power(g,12)
                profiles[idx]=dict(transitions=t,symbol_ranks=[len({r[b] for r in t}) for b in (0,1)],
                    rank_10_12=len(set(fp)),rank_01_12=len(set(gp)),
                    idempotent_10_12=power(fp,2)==fp,idempotent_01_12=power(gp,2)==gp,
                    image_10_12=fp,image_01_12=gp)
            idx+=1
    assert idx==166152 and len(profiles)==116
    result={'lemma_map_counts':check_lemma(),'profiles':profiles}
    for label,pair in [('champion',(U,V)),('warm64',(WU,WV))]:
        selected=[profiles[int(i)] for i in bypair[pair]]
        result[label]=dict(symbol_rank_counts=dict(Counter(str(r['symbol_ranks']) for r in selected)),
            power_rank_counts=dict(Counter(str((r['rank_10_12'],r['rank_01_12'])) for r in selected)),
            idempotent_count=sum(r['idempotent_10_12'] and r['idempotent_01_12'] for r in selected))
    result['elapsed_seconds']=time.monotonic()-started
    atomic_json(Path('results/v6_power.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k!='profiles'},indent=2))


if __name__=='__main__':main()
