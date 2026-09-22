#!/usr/bin/env python3
"""Ten-prototype certificate for the conceptual count 12 + 40 = 52.

This does not enumerate canonical DFAs.  Rank(f)=4 and rank(f^12)=2 force
two functional-graph shapes; pointing the start gives ten prototypes.  The
only finite audit is the 5! permutations p for each prototype.
"""
from collections import Counter
import itertools
import json
from pathlib import Path

from analyze_v2_permutation_structure import (
    U, V, compose, endpoint, power, rooted_canonical,
)


ROLES = ('a', 'b', 'x1', 'x2', 'x3')
KINDS = ('two_fixed_points', 'two_cycle')


def prototype(kind, start_role):
    order = (start_role,) + tuple(role for role in ROLES if role != start_role)
    index = {role: i for i, role in enumerate(order)}
    target = {
        'a': 'a' if kind == 'two_fixed_points' else 'b',
        'b': 'b' if kind == 'two_fixed_points' else 'a',
        'x1': 'a', 'x2': 'x1', 'x3': 'x2',
    }
    f = tuple(index[target[role]] for role in order)
    return f, order, index


def maps_and_table(f, p):
    pinv = tuple(p.index(q) for q in range(5))
    t0 = compose(f, pinv)
    table = tuple(zip(t0, p))
    e = power(f, 12)
    h = compose(power(f, 4), compose(
        pinv, compose(power(f, 5), compose(p, power(f, 2)))))
    return table, e, h


def accessible(table):
    seen = {0}
    stack = [0]
    while stack:
        q = stack.pop()
        for target in table[q]:
            if target not in seen:
                seen.add(target)
                stack.append(target)
    return len(seen) == 5


def named_fibres(kind, index):
    if kind == 'two_fixed_points':
        return ({index[r] for r in ('a', 'x1', 'x2', 'x3')},
                {index['b']})
    return ({index[r] for r in ('a', 'x2')},
            {index[r] for r in ('b', 'x1', 'x3')})


def fibre_index(q, fibres):
    return 0 if q in fibres[0] else 1


def fixed_point_incidence_formula(p, index):
    """K(x1) != K(a) in the two-fixed-point prototype."""
    fibre_a = {index[r] for r in ('a', 'x1', 'x2', 'x3')}
    a, b, x1 = (index[r] for r in ('a', 'b', 'x1'))
    return p[b] == a and ((p[x1] in fibre_a) != (p[a] in fibre_a))


def two_cycle_incidence_formula(p, index):
    """The two independent cross-fibre incidences for the 2-cycle."""
    fibre_a = {index[r] for r in ('a', 'x2')}
    a, b, x1 = (index[r] for r in ('a', 'b', 'x1'))
    pinv = tuple(p.index(q) for q in range(5))
    images_cross = (p[x1] in fibre_a) != (p[b] in fibre_a)
    representative_preimages_cross = ((pinv[a] in fibre_a) !=
                                      (pinv[b] in fibre_a))
    return images_cross and representative_preimages_cross


def compact_record(record):
    return {
        'p_in_prototype_coordinates': record['p'],
        'transitions_in_prototype_coordinates': record['table'],
        'canonical_transitions': rooted_canonical(record['table']),
        'e_in_prototype_coordinates': record['e'],
        'h_in_prototype_coordinates': record['h'],
        'separated': record['separated'],
    }


def audit():
    prototype_rows = []
    fixed_leaf_records = []
    total_accessible = 0
    total_separating = 0

    for kind in KINDS:
        for start_role in ROLES:
            f, order, index = prototype(kind, start_role)
            fibres = named_fibres(kind, index)
            counts = Counter()
            records = []
            for p in itertools.permutations(range(5)):
                table, e, h = maps_and_table(f, p)
                separated = endpoint(table, U) != endpoint(table, V)
                certificate = h[e[0]] != e[h[0]]
                assert separated == certificate
                assert compose(e, e) == e
                assert power(f, 4) == e
                assert all(h[q] in set(e) for q in range(5))

                if kind == 'two_fixed_points':
                    formula = (start_role == 'x3' and
                               fixed_point_incidence_formula(p, index))
                else:
                    formula = (start_role == 'x3' and
                               two_cycle_incidence_formula(p, index))
                assert separated == formula

                is_accessible = accessible(table)
                if is_accessible:
                    pair = (fibre_index(h[0], fibres),
                            fibre_index(h[e[0]], fibres))
                    counts[pair] += 1
                    records.append(dict(p=p, table=table, e=e, h=h,
                                        separated=separated))

            accessible_count = sum(counts.values())
            separating_count = sum(count for (i, j), count in counts.items()
                                   if i != j)
            total_accessible += accessible_count
            total_separating += separating_count
            prototype_rows.append({
                'kind': kind,
                'start_role': start_role,
                'accessible_permutations': accessible_count,
                'separating_permutations': separating_count,
                'named_fibre_bucket_counts': {
                    str(key): counts[key] for key in sorted(counts)
                },
            })
            if kind == 'two_fixed_points' and start_role == 'x3':
                fixed_leaf_records = records

    assert total_accessible == 829
    assert total_separating == 52
    assert sum(row['separating_permutations'] for row in prototype_rows
               if row['kind'] == 'two_fixed_points') == 12
    assert sum(row['separating_permutations'] for row in prototype_rows
               if row['kind'] == 'two_cycle') == 40

    smallest_nonseparator = min(
        (record for record in fixed_leaf_records if not record['separated']),
        key=lambda record: rooted_canonical(record['table']))
    smallest_separator = min(
        (record for record in fixed_leaf_records if record['separated']),
        key=lambda record: rooted_canonical(record['table']))

    return {
        'schema_version': 1,
        'method': 'two functional-graph shapes, five pointed roles, 5! permutations each',
        'prototype_count': 10,
        'permutations_per_prototype': 120,
        'total_small_checks': 1200,
        'accessible_total': total_accessible,
        'separator_total': total_separating,
        'conceptual_count': {
            'two_fixed_points': {
                'formula': '2 choices for which of x1,a maps to b; 3 choices for the other image; 2! remaining',
                'count_expression': '2*3*2',
                'count': 12,
            },
            'two_cycle': {
                'formula': 'opposite representative preimages in A,B: 16 in orientation AB and 24 in orientation BA',
                'count_expression': '16+24',
                'count': 40,
            },
            'total_expression': '12+40',
            'total': 52,
        },
        'prototype_rows': prototype_rows,
        'falsified_leaf_sufficiency': {
            'statement': 'rank(e)=2 and start_role=x3 suffice for separation',
            'same_kind': 'two_fixed_points',
            'same_start_role': 'x3',
            'nonseparating': compact_record(smallest_nonseparator),
            'separating': compact_record(smallest_separator),
        },
    }


def main():
    result = audit()
    Path('results/v2_rank2_conceptual_count.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
