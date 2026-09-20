#!/usr/bin/env python3
"""Exact 120-table permutation branch of the shared-block obstruction.

If both letters permute <=5 states, (10)^12 and (01)^12 are identities
unless their two-letter maps are 5-cycles. Only this branch can separate
(10)^12 B from B (01)^12, for ANY B.
"""
import itertools
from pathlib import Path
from separating_words.enumerate_dfa import canonicalize
from analyze_v6_power import is_full_five_cycle
from analyze_v6_exchange import atomic_json


def permutation_pool():
    permutations=list(itertools.permutations(range(5)));tables=set();labeled=0
    for t0 in permutations:
        for t1 in permutations:
            if is_full_five_cycle(tuple(t0[t1[q]] for q in range(5))):
                tables.add(canonicalize(tuple(zip(t0,t1))));labeled+=1
    assert labeled==2880 and len(tables)==120
    return sorted(tables)


if __name__=='__main__':
    tables=permutation_pool()
    atomic_json(Path('results/v6_permutation_pool.json'),dict(
        count=len(tables),labeled_count=2880,transitions=tables,
        scope='Complete permutation-DFA obstruction pool for the aligned shared-block family, any B. Not a sufficient global verifier.'))
    print('120 canonical accessible permutation tables; 2880 labeled tables.')
