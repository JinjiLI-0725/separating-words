#!/usr/bin/env python3
"""Bounded exact witness-exchange study; no SAT or witness-only filtering.

Global IDs concatenate canonical generator order for k=1,...,5 (zero based).
Rows store exact sets in compressed NPZ, metadata in JSONL; resume is automatic.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import itertools
import gzip
import json
from pathlib import Path
import time
import numpy as np
from separating_words.canonical_generator import generate_canonical_dfas
from search_v4_4_witness_guided import endpoint_matrix, materialize_automata, flip_many

U = '10101010101010101010101010101101010101001010101'
V = '10101101010101001010101010101010101010101010101'
WU = '10101010101010101010101010101001011101001010101'
WV = '10101001011101001010101010101010101010101010101'
A, B, C = U[:24], U[24:], V[23:]
assert U == A+B and V == B+C
N = 166152


def atomic_json(path, obj):
    tmp = path.with_suffix('.tmp')
    if path.suffix=='.gz':
        tmp.write_bytes(gzip.compress(json.dumps(obj,separators=(',',':')).encode(),compresslevel=1))
    else:
        tmp.write_text(json.dumps(obj, indent=2)+'\n')
    tmp.replace(path)


def family():
    out = {}
    def add(u, v, kind, **kw):
        assert len(u) == len(v) == 47
        if u != v:
            out.setdefault((u,v), []).append(dict(type=kind, **kw))
    add(U,V,'champion'); add(WU,WV,'warm64')
    # Complete degree <=2 perturbations of the shared 23-symbol block.
    for degree in (1,2):
        for positions in itertools.combinations(range(23), degree):
            b = flip_many(B, positions)
            add(A+b,b+C,'aligned24',positions=positions)
    # Matched controls: +/-2 offset errors, opposite alignment, same position,
    # and unilateral flips. Exact sets, rather than old stored scalar scores.
    for d in (0,22,26,-24):
        for j in range(47):
            i=j+d
            if 0 <= i < 47:
                add(flip_many(U,[i]),flip_many(V,[j]),'offset_control',offset=d,i=i,j=j)
    for i in range(47):
        add(flip_many(U,[i]),V,'asymmetric',side='u',position=i)
        add(U,flip_many(V,[i]),'asymmetric',side='v',position=i)
    # Preserve length while moving symbols/short blocks within B.
    # Positions near the two phase defects, with both movement directions.
    for width in (1,2):
        for start in (3,4,5,6,9,10,13,14,15,16):
            for delta in (-2,-1,1,2):
                stop=start+width; dest=start+delta
                rest=B[:start]+B[stop:]
                b=rest[:dest]+B[start:stop]+rest[dest:]
                add(A+b,b+C,'block_move',start=start,width=width,delta=delta)
    # Transfer an alternating 2-symbol block between flanks of each word.
    for shift in (-4,-2,2,4):
        def slide(w,s):
            return w[s:]+w[:s]
        add(slide(U,shift),slide(V,shift),'cyclic_shift',shift=shift)
        add(slide(U,shift),V,'asymmetric_shift',side='u',shift=shift)
        add(U,slide(V,shift),'asymmetric_shift',side='v',shift=shift)
    return out


def scalar_verify(u,v):
    """Independent scalar state simulation, without optimized scorer/padding."""
    found=[]; counts={}; idx=0
    for k in range(1,6):
        count=0
        for t in generate_canonical_dfas(k):
            x=y=0
            for a,b in zip(u,v):
                x=t[x][int(a)]; y=t[y][int(b)]
            if x!=y: found.append(idx)
            idx+=1; count+=1
        counts[k]=count
    assert list(counts.values()) == [1,12,216,5248,160675]
    return found


def summarize(rows, masks, old, prefix):
    M=np.stack(masks)
    oldmask=np.zeros(N,dtype=bool);oldmask[old]=True
    # Witness families are identical incidence columns, NOT state conjugacy.
    active=np.flatnonzero(M.any(axis=0))
    signatures=np.packbits(M[:,active],axis=0).T
    groups=defaultdict(list)
    for idx,sig in zip(active,signatures):
        groups[(bool(oldmask[idx]),sig.tobytes())].append(int(idx))
    families=[]; edges=[{'candidate':i,'eliminated_old_groups':[],'introduced_new_groups':[]} for i in range(len(rows))]
    for _key,ids in sorted(groups.items(),key=lambda kv:(not kv[0][0],-len(kv[1]),kv[1][0])):
        gid=len(families); isold=bool(oldmask[ids[0]])
        occurs=np.flatnonzero(M[:,ids[0]]).tolist()
        families.append(dict(id=gid,old=isold,size=len(ids),witness_ids=ids,candidates=occurs))
        targets=np.flatnonzero(~M[:,ids[0]]) if isold else occurs
        for i in targets: edges[i]['eliminated_old_groups' if isold else 'introduced_new_groups'].append(gid)
    # Include any never-retained old witnesses (champion ensures none here).
    newsets=defaultdict(list)
    for i,m in enumerate(M): newsets[np.packbits(m & ~oldmask).tobytes()].append(i)
    recurring=[dict(candidates=ids,new_count=rows[ids[0]]['introduced']) for ids in newsets.values() if len(ids)>1]
    bytype=defaultdict(set)
    for i,r in enumerate(rows):
        for m in r['mutations']: bytype[m['type']].add(i)
    types={t:dict(count=len(ids),minimum=min(rows[i]['score'] for i in ids),median=float(np.median([rows[i]['score'] for i in ids])),zero_old=sum(rows[i]['retained']==0 for i in ids)) for t,ids in bytype.items()}
    low=[i for i,r in enumerate(rows) if r['score']<=200]
    # Compact exact signatures restricted to low-score candidates are often
    # more useful than groups split by high-score controls.
    lowgroups=defaultdict(list)
    for idx in np.flatnonzero(M[low].any(axis=0)):
        lowgroups[(bool(oldmask[idx]),np.packbits(M[low,idx]).tobytes())].append(int(idx))
    lowfamilies=[dict(old=key[0],size=len(ids),witness_ids=ids,candidates=[low[j] for j in np.flatnonzero(M[low,ids[0]])]) for key,ids in lowgroups.items()]
    lowfamilies.sort(key=lambda x:-x['size'])
    # Greedy cover is a reproducible finite-family certificate, not a theorem.
    uncovered=set(range(len(rows)));cover=[]
    while uncovered:
        counts=M[sorted(uncovered)].sum(axis=0);w=int(counts.argmax())
        if counts[w]==0: break
        hit=set(np.flatnonzero(M[:,w])) & uncovered
        cover.append(dict(witness=w,candidates=sorted(map(int,hit))))
        uncovered-=hit
    summary=dict(candidate_count=len(rows),best_score=min(r['score'] for r in rows),types=types,
        old_groups=sum(f['old'] for f in families),new_groups=sum(not f['old'] for f in families),
        witness_union=len(active),new_witness_union=int((M.any(axis=0)&~oldmask).sum()),
        recurring_new_sets=recurring,low_score_candidates=low,low_score_families=lowfamilies,
        greedy_cover=cover,uncovered=sorted(uncovered),
        top=sorted(range(len(rows)),key=lambda i:rows[i]['score'])[:30])
    atomic_json(prefix.with_suffix('.summary.json'),summary)
    atomic_json(prefix.with_suffix('.graph.json.gz'),dict(families=families,edges=edges))
    return summary


def run(candidates, prefix, seconds=900, reuse_prefix=None):
    candidates=dict(candidates)
    candidates.setdefault((U,V),[{"type":"champion"}])
    started=time.monotonic();prefix.parent.mkdir(exist_ok=True)
    previous_summary=prefix.with_suffix('.summary.json')
    prior_runs=[]
    if previous_summary.exists():
        previous=json.loads(previous_summary.read_text())
        prior_runs=previous.get('runs',[dict(elapsed_seconds=previous.get('elapsed_seconds',json.loads(prefix.with_suffix('.checkpoint.json').read_text())['elapsed_seconds']),completed=previous['candidate_count'])])
    T=materialize_automata()
    E=endpoint_matrix(T,[U,V,WU,WV])
    old=np.flatnonzero(E[0]!=E[1]); warm=np.flatnonzero(E[2]!=E[3])
    assert len(old)==52 and len(warm)==64 and not np.intersect1d(old,warm).size
    assert np.all(old>=5477)
    rows=[];masks=[];done=set()
    path=prefix.with_suffix('.jsonl'); sets=prefix.with_suffix('.sets.npz')
    if path.exists():
        rows=[json.loads(s) for s in path.read_text().splitlines()]
        M=np.unpackbits(np.load(sets)['packed'],axis=1,count=N).astype(bool)
        assert len(M)>=len(rows)
        masks=list(M[:len(rows)]);done={(r['u'],r['v']) for r in rows}
    # Reuse existing beam witness sets; endpoint details are optional on reused rows.
    prior=json.loads(Path('results/v4_5_beam.json').read_text())
    cache={(r['u'],r['v']):r['witness_indices'] for r in prior['final_beam']+[prior['best_ever']]}
    if reuse_prefix is not None:
        previous=[json.loads(s) for s in reuse_prefix.with_suffix(".jsonl").read_text().splitlines()]
        previous_sets=np.unpackbits(np.load(reuse_prefix.with_suffix(".sets.npz"))["packed"],axis=1,count=N)
        assert len(previous)==len(previous_sets)
        for row,mask in zip(previous,previous_sets):
            cache[row["u"],row["v"]]=np.flatnonzero(mask).tolist()
    for j,pair in enumerate([(U,V),(WU,WV)]):
        cache[pair]=[int(x) for x in (old if j==0 else warm)]
    initial_count=len(rows)
    pending=[p for p in candidates if p not in done]
    def save():
        tmp=path.with_suffix('.tmp');tmp.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        # Sets first: interruption between files is detected on resume.
        set_tmp=sets.with_suffix('.tmp')
        with set_tmp.open('wb') as f:
            np.savez_compressed(f,packed=np.packbits(np.stack(masks),axis=1))
        set_tmp.replace(sets)
        tmp.replace(path)
        atomic_json(prefix.with_suffix('.checkpoint.json'),dict(completed=len(rows),pending=len(candidates)-len(rows),elapsed_seconds=time.monotonic()-started))
    zero=False
    for offset in range(0,len(pending),24):
        batch=pending[offset:offset+24]
        words=sorted({w for pair in batch if pair not in cache for w in pair})
        ix={w:i for i,w in enumerate(words)}
        endpoints=endpoint_matrix(T,words) if words else None
        for u,v in batch:
            mask=np.zeros(N,dtype=bool);ep=None
            if (u,v) in cache:
                mask[cache[u,v]]=True;source='reused exact set'
            else:
                eu,ev=endpoints[ix[u]],endpoints[ix[v]];mask=eu!=ev
                ep=dict(Counter(f'{int(a)},{int(b)}' for a,b in zip(eu[mask],ev[mask])))
                source='NumPy exhaustive endpoints'
            score=int(mask.sum()); retained=int(mask[old].sum());introduced=score-retained
            row=dict(id=len(rows),u=u,v=v,score=score,retained=retained,eliminated=52-retained,introduced=introduced,
                intersection=retained,union=52+introduced,jaccard=retained/(52+introduced),
                mutations=candidates[u,v],endpoint_patterns=ep,source=source,
                by_k=[int(mask[a:b].sum()) for a,b in zip([0,1,13,229,5477],[1,13,229,5477,N])])
            rows.append(row);masks.append(mask)
            if score<52:
                save(); evidence=prefix.with_suffix(f'.improvement_{row["id"]}.json')
                atomic_json(evidence,dict(candidate=row,status='awaiting scalar verification',witness_ids=np.flatnonzero(mask).tolist()))
                independent=scalar_verify(u,v)
                assert independent==np.flatnonzero(mask).tolist()
                atomic_json(evidence,dict(candidate=row,status='independently verified',witness_ids=independent))
                if score==0: zero=True;break
        save()
        print(f'{prefix.name}: {len(rows)}/{len(candidates)} best={min(r["score"] for r in rows)} elapsed={time.monotonic()-started:.1f}s',flush=True)
        if zero or time.monotonic()-started>seconds: break
    summary=summarize(rows,masks,old,prefix)
    runs=prior_runs+[dict(elapsed_seconds=time.monotonic()-started,completed=len(rows)-initial_count)]
    summary.update(elapsed_seconds=sum(r['elapsed_seconds'] for r in runs),runs=runs,complete=len(rows)==len(candidates),regressions={'champion':52,'warm':64,'overlap':0})
    atomic_json(prefix.with_suffix('.summary.json'),summary)
    print(json.dumps({k:summary[k] for k in ('candidate_count','best_score','types','elapsed_seconds')},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prefix',default='results/v6_1_exchange');parser.add_argument('--seconds',type=float,default=900)
    parser.add_argument('--candidates',type=Path);parser.add_argument('--reuse-prefix',type=Path)
    args=parser.parse_args()
    candidates=family() if args.candidates is None else {(r['u'],r['v']):r['mutations'] for r in json.loads(args.candidates.read_text())['candidates']}
    run(candidates,Path(args.prefix),args.seconds,args.reuse_prefix)
