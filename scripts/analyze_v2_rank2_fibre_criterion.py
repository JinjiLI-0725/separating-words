#!/usr/bin/env python3
"""Exact fibre criterion for the rank-2 e=f^12 slice.

This is a fixed-word structural enumeration of the 829 canonical tables
already isolated by the rank-4/T1-permutation reduction.  It does not search
for words or enumerate candidate word pairs.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path

from separating_words.canonical_generator import generate_canonical_dfas
from analyze_v2_rank2_classification import structural_row


def rows():
    out = []
    for t in generate_canonical_dfas(5):
        t0 = tuple(row[0] for row in t)
        p = tuple(row[1] for row in t)
        if len(set(t0)) != 4 or len(set(p)) != 5:
            continue
        row = structural_row(t)
        if len(set(row['e'])) != 2:
            continue
        image = tuple(row['image'])
        fibre_index = lambda q: image.index(row['e'][q])
        # j is defined because h(e(0)) is in Im(e); the script verifies this
        # exact dynamical fact over every row below.
        i = fibre_index(row['h'][0])
        s = row['h'][row['e'][0]]
        assert s in image
        j = image.index(s)
        row['h0_fibre'] = i
        row['h_e0_image_index'] = j
        out.append(row)
    return out


def smallest(rows, predicate):
    choices = [row for row in rows if predicate(row)]
    return min(choices, key=lambda row: row['transitions'])


def compact(row):
    return {
        'transitions': row['transitions'],
        'e': row['e'],
        'h': row['h'],
        'separated': row['separated'],
        'zero_fibre': row['zero_fibre'],
        'h0_fibre': row['h0_fibre'],
        'h_e0_image_index': row['h_e0_image_index'],
    }


def main():
    data = rows()
    assert len(data) == 829
    assert all(row['h'][row['e'][0]] in row['image'] for row in data)

    exact_buckets = defaultdict(set)
    for row in data:
        key = (row['h0_fibre'], row['h_e0_image_index'])
        exact_buckets[key].add(row['separated'])
    assert len(exact_buckets) == 4
    assert all(len(labels) == 1 for labels in exact_buckets.values())
    assert all((i != j) == next(iter(labels))
               for (i, j), labels in exact_buckets.items())

    # These are deliberately weaker proposed criteria.  Store the smallest
    # exact opposite-label examples, so future changes cannot hide their
    # failure behind aggregate counts.
    coarse_buckets = defaultdict(list)
    for row in data:
        coarse_buckets[(row['zero_fibre'], row['h0_fibre'])].append(row)
    coarse_conflicts = [group for group in coarse_buckets.values()
                        if len({row['separated'] for row in group}) > 1]
    assert coarse_conflicts
    coarse_group = min(coarse_conflicts,
                        key=lambda group: min(row['transitions'] for row in group))
    rank2_counterexample = smallest(data, lambda row: not row['separated'])

    result = {
        'schema_version': 1,
        'universe': '829 canonical accessible rank-4/T1-permutation tables with rank(e)=2',
        'criterion': 'fibre_index(h(0)) != image_index(h(e(0)))',
        'proof_input': 'h(e(0)) is in Im(e) because h starts with f^4 and Im(e) is the f-cycle set',
        'universe_count': len(data),
        'separator_count': sum(row['separated'] for row in data),
        'h_e0_in_image_count': sum(row['h'][row['e'][0]] in row['image']
                                   for row in data),
        'criterion_bucket_counts': {
            str(key): {
                'count': sum((row['h0_fibre'], row['h_e0_image_index']) == key
                             for row in data),
                'separating': sum(row['separated'] and
                                  (row['h0_fibre'], row['h_e0_image_index']) == key
                                  for row in data),
            }
            for key in sorted(exact_buckets)
        },
        'weaker_candidate_counterexamples': {
            'rank_e_2_is_sufficient': compact(rank2_counterexample),
            'zero_fibre_and_h0_fibre_is_sufficient': {
                'same_signature': [coarse_group[0]['zero_fibre'],
                                   coarse_group[0]['h0_fibre']],
                'separating': compact(smallest(coarse_group, lambda row: row['separated'])),
                'nonseparating': compact(smallest(coarse_group, lambda row: not row['separated'])),
            },
        },
    }
    Path('results/v2_rank2_fibre_criterion.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
