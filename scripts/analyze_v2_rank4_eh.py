#!/usr/bin/env python3
"""Analyze the rank-4 branch through e=f^12 and h.

This is deliberately a fixed-word enumeration, not a word search.  The
criterion checked here is the exact pointed reduction from the V2 note:

    U(0) != V(0)  iff  h(e(0)) != e(h(0)).

Run from the repository root with PYTHONPATH=src.
"""
from collections import Counter
import json
from pathlib import Path

from separating_words.canonical_generator import generate_canonical_dfas
from analyze_v2_permutation_structure import compose, power, endpoint, U, V


def eh_maps(t):
    t0 = tuple(row[0] for row in t)
    p = tuple(row[1] for row in t)
    f = compose(t0, p)
    pinv = tuple(p.index(q) for q in range(5))
    h = compose(power(f, 4), compose(pinv, compose(power(f, 5),
                                                   compose(p, power(f, 2)))))
    return f, power(f, 12), h


def main():
    rows = []
    for t in generate_canonical_dfas(5):
        t0 = tuple(row[0] for row in t)
        p = tuple(row[1] for row in t)
        if len(set(t0)) != 4 or len(set(p)) != 5:
            continue
        f, e, h = eh_maps(t)
        separated = endpoint(t, U) != endpoint(t, V)
        certificate = h[e[0]] != e[h[0]]
        assert compose(e, e) == e
        assert separated == certificate
        rows.append(dict(transitions=t, f=f, e=e, h=h,
                         e_image=sorted(set(e)),
                         e_kernel_sizes=sorted(Counter(e).values()),
                         e_rank=len(set(e)), h_rank=len(set(h)),
                         separated=separated,
                         incidence=dict(e0=e[0], h0=h[0],
                                        h_e0=h[e[0]], e_h0=e[h[0]])))

    champion = [row for row in rows if row['separated']]
    result = dict(
        schema_version=1,
        words=dict(U=U, V=V),
        criterion='h(e(0)) != e(h(0))',
        universe_count=len(rows),
        separator_count=len(champion),
        e_idempotent_for_all=True,
        e_rank_counts=dict(sorted(Counter(row['e_rank'] for row in rows).items())),
        e_kernel_partition_counts={
            str(key): value for key, value in sorted(
                Counter(tuple(row['e_kernel_sizes']) for row in rows).items())
        },
        champion_e_rank_counts=dict(sorted(Counter(row['e_rank'] for row in champion).items())),
        champion_h_rank_counts=dict(sorted(Counter(row['h_rank'] for row in champion).items())),
        champion_e_kernel_partition_counts={
            str(key): value for key, value in sorted(
                Counter(tuple(row['e_kernel_sizes']) for row in champion).items())
        },
        champion_incidence=Counter(
            (row['incidence']['e0'], row['incidence']['h0'],
             row['incidence']['h_e0'], row['incidence']['e_h0'])
            for row in champion
        ),
        champion=champion,
    )
    # JSON has no tuple keys; make the small summary counters explicit.
    result['champion_incidence'] = [
        dict(zip(('e0', 'h0', 'h_e0', 'e_h0'), key), count=count)
        for key, count in sorted(result['champion_incidence'].items())
    ]
    path = Path('results/v2_rank4_eh.json')
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in (
        'universe_count', 'separator_count', 'e_rank_counts',
        'champion_e_rank_counts', 'champion_h_rank_counts')}, indent=2))


if __name__ == '__main__':
    main()
