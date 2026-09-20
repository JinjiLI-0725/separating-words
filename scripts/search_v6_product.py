#!/usr/bin/env python3
"""Nearest shared blocks evading a small exact exchange-cover DFA product.

Dynamic programming counts all 2^23 shared blocks by Hamming distance, using
only reachable product states. Only a bounded set of NEW closest escapes is
emitted for subsequent full NumPy scoring. No SAT and no global-score claims.
"""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import time
from separating_words.canonical_generator import generate_canonical_dfas
from analyze_v6_exchange import A,B,C,U,V,atomic_json,family
from analyze_v6_structure import read,cover


def run_word(t,w,q=0):
    for c in w: q=t[q][int(c)]
    return q


def product_candidates(tables, center, prefix, suffix, excluded, cap=48, seconds=90):
    start_time=time.monotonic(); n=len(center); visited=0
    start=tuple(q for t in tables for q in (run_word(t,prefix),0))
    end_maps=[tuple(run_word(t,suffix,q) for q in range(len(t))) for t in tables]
    @lru_cache(None)
    def step(state,bit):
        return tuple(tables[i//2][q][bit] for i,q in enumerate(state))
    def accepts(state):
        return all(state[2*i]==end_maps[i][state[2*i+1]] for i in range(len(tables)))
    @lru_cache(None)
    def count(pos,state,distance):
        nonlocal visited
        visited+=1
        if visited%4096==0 and time.monotonic()-start_time>seconds:
            raise TimeoutError('product DP budget exceeded')
        if distance<0 or distance>n-pos: return 0
        if pos==n: return int(distance==0 and accepts(state))
        return sum(count(pos+1,step(state,bit),distance-(bit!=int(center[pos]))) for bit in (0,1))
    histogram=[count(0,start,d) for d in range(n+1)]
    selected=[];skipped_known=0;skipped_equal=0
    def emit(pos,state,distance,word):
        nonlocal skipped_known,skipped_equal
        if len(selected)>=cap:return
        if not count(pos,state,distance):return
        if pos==n:
            pair=(prefix+word,word+suffix)
            if pair[0]==pair[1]:skipped_equal+=1
            elif pair in excluded:skipped_known+=1
            else:selected.append(dict(u=pair[0],v=pair[1],mutations=[dict(type='product_escape',positions=[i for i,(a,b) in enumerate(zip(center,word)) if a!=b])]))
            return
        for bit in (int(center[pos]),1-int(center[pos])):
            emit(pos+1,step(state,bit),distance-(bit!=int(center[pos])),word+str(bit))
    for d in range(n+1):
        emit(0,start,d,'')
        if len(selected)>=cap: break
    return dict(candidates=selected,escape_counts_by_distance=histogram,total_block_escapes=sum(histogram),
        skipped_known=skipped_known,skipped_equal=skipped_equal,dp_cache_states=count.cache_info().currsize,
        transition_cache_states=step.cache_info().currsize,dp_seconds=time.monotonic()-start_time)


def main():
    p=argparse.ArgumentParser();p.add_argument('prefix',type=Path);p.add_argument('--output',type=Path,default=Path('results/v6_2_product_candidates.json'));p.add_argument('--cap',type=int,default=48)
    args=p.parse_args();started=time.monotonic()
    rows,M=read(args.prefix); low=[i for i,r in enumerate(rows) if r['score']<=200]
    certificate=cover(M[low]);ids=certificate['exact_witness_ids'] or certificate['greedy_witness_ids']
    # Keep product bounded. If more than three witnesses are needed, explicitly
    # use a partial cover and do not claim every low candidate is excluded.
    ids=ids[:3];tables={};index=0
    for k in range(1,6):
        for t in generate_canonical_dfas(k):
            if index in ids:tables[index]=t
            index+=1
            if len(tables)==len(ids):break
        if len(tables)==len(ids):break
    excluded={(r['u'],r['v']) for r in rows} | set(family())
    # Avoid re-running scalar-only older searches: their global score is known.
    for name in ['v4_1_fast_scored_neighbors.json','v4_2_batch_local.json','v4_4_witness_guided.json']:
        old=json.loads((Path('results')/name).read_text())
        for r in old.get('ranking',old.get('top',[])):excluded.add((r['u'],r['v']))
    prior_beam=json.loads(Path('results/v4_5_beam.json').read_text())
    excluded.update((r['u'],r['v']) for r in prior_beam['final_beam'])
    result=product_candidates([tables[i] for i in ids],B,A,C,excluded,args.cap)
    # Scalar validation of all emitted product escapes.
    for r in result['candidates']:
        assert all(run_word(t,r['u'])==run_word(t,r['v']) for t in tables.values())
    result.update(witness_ids=ids,transitions={str(i):tables[i] for i in ids},source=str(args.prefix),source_snapshot_candidates=len(rows),
        low_score_cover=certificate,complete_cover_used=len(ids)==(certificate['exact_minimum'] or certificate['greedy_size']),
        elapsed_seconds=time.monotonic()-started)
    atomic_json(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('candidates','transitions')},indent=2))


if __name__=='__main__':main()
