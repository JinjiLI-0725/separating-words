"""Ground-truth regressions and independent small-DFA endpoint comparison."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_v6_exchange import U,V,WU,WV,family
from search_v4_4_witness_guided import endpoint_matrix,materialize_automata
from separating_words.canonical_generator import generate_canonical_dfas


def test_v6_exact_regressions():
    T=materialize_automata()
    E=endpoint_matrix(T,[U,V,WU,WV])
    old=E[0]!=E[1]; warm=E[2]!=E[3]
    assert old.sum()==52
    assert warm.sum()==64
    assert not (old & warm).any()
    assert not old[:5477].any()


def test_endpoint_batch_boundaries_against_scalar():
    tables=list(generate_canonical_dfas(3))
    words=['000','001','010','011','100','101','110','111']
    expected=[]
    for w in words:
        row=[]
        for t in tables:
            q=0
            for ch in w: q=t[q][int(ch)]
            row.append(q)
        expected.append(row)
    assert np.array_equal(endpoint_matrix(np.array(tables),words,17,3),expected)


def test_family_is_bounded_and_nontrivial():
    candidates=family()
    assert 400<len(candidates)<800
    assert (U,V) in candidates and (WU,WV) in candidates
    assert all(len(u)==len(v)==47 and u!=v for u,v in candidates)


def test_finite_cover_certificates():
    from analyze_v6_structure import cover
    assert cover(np.array([[1,0],[1,1]],dtype=bool))['exact_minimum']==1
    assert cover(np.eye(2,dtype=bool))['exact_minimum']==2
    c=cover(np.eye(3,dtype=bool))
    assert c['exact_minimum'] is None and c['lower_bound']==c['greedy_size']==3


def test_product_dp_matches_exhaustive_small_blocks():
    import itertools
    from search_v6_product import product_candidates,run_word
    tables=[((1,0),(0,1)),((1,0),(1,0))]
    center='0101';prefix='10';suffix='01'
    expected=[0]*5
    for bits in itertools.product('01',repeat=4):
        b=''.join(bits)
        if all(run_word(t,prefix+b)==run_word(t,b+suffix) for t in tables):
            expected[sum(x!=y for x,y in zip(b,center))]+=1
    result=product_candidates(tables,center,prefix,suffix,set(),cap=100)
    assert result['escape_counts_by_distance']==expected
    assert all(r['u']!=r['v'] for r in result['candidates'])


def test_twelfth_power_lemma_exhaustive_maps():
    from analyze_v6_power import check_lemma
    result=check_lemma()
    assert [r['non_idempotent_12th_powers'] for r in result.values()]==[0,0,0,0,24]


def test_complete_permutation_obstruction_pool():
    from build_v6_permutation_pool import permutation_pool
    from analyze_v6_power import is_full_five_cycle
    pool=permutation_pool()
    assert len(pool)==120 and len(set(pool))==120
    for t in pool:
        assert all(len({r[b] for r in t})==5 for b in (0,1))
        assert is_full_five_cycle(tuple(t[t[q][1]][0] for q in range(5)))
