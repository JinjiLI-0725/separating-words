#!/usr/bin/env python3
"""Exhaustive structural certificate for the 52 rank-2 witnesses.

The search space here is only the 829 canonical rank-4/T1-permutation
tables with rank(f^12)=2.  No word search and no enumeration of all
166,152 accessible tables is used.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path

from separating_words.canonical_generator import generate_canonical_dfas
from analyze_v2_rank4_eh import eh_maps
from analyze_v2_permutation_structure import endpoint, U, V


def cycle_type(p):
    unseen, out = set(range(5)), []
    while unseen:
        q, size = min(unseen), 0
        while q in unseen:
            unseen.remove(q)
            size += 1
            q = p[q]
        out.append(size)
    return tuple(sorted(out))


def structural_row(t):
    f, e, h = eh_maps(t)
    image = tuple(sorted(set(e)))
    fibres = tuple(tuple(q for q, value in enumerate(e) if value == a)
                   for a in image)
    quotient = lambda q: image.index(e[q])
    # This is a fibrewise signature, not an assumed quotient action: h can
    # send different points of one fibre to different e-fibres.
    h_fibre_action = tuple(tuple(quotient(h[q]) for q in fibre)
                           for fibre in fibres)
    p = tuple(row[1] for row in t)
    separated = endpoint(t, U) != endpoint(t, V)
    certificate = h[e[0]] != e[h[0]]
    assert separated == certificate
    return dict(
        transitions=t, e=e, h=h, image=image,
        fibre_sizes=tuple(map(len, fibres)),
        zero_fibre=next(i for i, fibre in enumerate(fibres) if 0 in fibre),
        h_fibre_action=h_fibre_action,
        t1_cycle_type=cycle_type(p), separated=separated,
    )


def bucket(rows, fields):
    out = defaultdict(set)
    for row in rows:
        out[tuple(row[field] for field in fields)].add(row['separated'])
    return out


def main():
    rows = []
    for t in generate_canonical_dfas(5):
        t0 = tuple(row[0] for row in t)
        p = tuple(row[1] for row in t)
        if len(set(t0)) != 4 or len(set(p)) != 5:
            continue
        row = structural_row(t)
        if len(set(row['e'])) != 2:
            continue
        rows.append(row)

    # The requested coarse data are deliberately tested as separate
    # candidates, including a combined coarse signature.
    coarse = ['image', 'fibre_sizes', 'zero_fibre', 't1_cycle_type']
    action = ['zero_fibre', 'h_fibre_action']
    coarse_buckets = bucket(rows, coarse)
    action_buckets = bucket(rows, action)
    assert len(rows) == 829
    assert sum(row['separated'] for row in rows) == 52
    assert sum(len(values) > 1 for values in coarse_buckets.values()) == 34
    assert sum(len(values) > 1 for values in action_buckets.values()) == 0

    positives = Counter(
        (row['zero_fibre'], row['h_fibre_action'])
        for row in rows if row['separated'])
    cases = []
    for (zero_fibre, h_fibre_action), count in sorted(positives.items()):
        by_cycle = Counter(
            row['t1_cycle_type'] for row in rows if row['separated']
            and row['zero_fibre'] == zero_fibre
            and row['h_fibre_action'] == h_fibre_action)
        cases.append(dict(zero_fibre=zero_fibre,
                          h_fibre_action=h_fibre_action,
                          count=count,
                          t1_cycle_type_counts={str(key): value for key, value
                                                in sorted(by_cycle.items())}))

    result = dict(
        schema_version=1,
        universe='canonical accessible 5-state tables, rank(T0)=4, T1 permutation',
        rank2_universe_count=len(rows), witness_count=sum(positives.values()),
        criterion='h(e(0)) != e(h(0))',
        coarse_fields=coarse,
        coarse_bucket_count=len(coarse_buckets),
        coarse_conflicting_bucket_count=sum(
            len(values) > 1 for values in coarse_buckets.values()),
        exact_fields=action,
        exact_bucket_count=len(action_buckets),
        exact_conflicting_bucket_count=sum(
            len(values) > 1 for values in action_buckets.values()),
        witness_case_count=len(cases), witness_cases=cases,
        witness_fibre_size_counts=dict(Counter(
            str(row['fibre_sizes']) for row in rows if row['separated'])),
        witness_t1_cycle_type_counts=dict(Counter(
            str(row['t1_cycle_type']) for row in rows if row['separated'])),
    )
    Path('results/v2_rank2_classification.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
