"""Independent finite checks for the V2 algebra and branch distinction."""
import csv
import itertools
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_v2_permutation_structure import (
    A, B, C, U, V, PERMS, compose, endpoint, power,
    reconstruct_pool, relabel, rooted_canonical, semigroup, word_map,
)


@pytest.fixture(scope='module')
def result():
    return json.loads(Path('results/v2_permutation_classification.json').read_text())


def test_independent_pool_enumeration_and_root_quotient(result):
    # Independent exhaustive pair construction, rather than solving for T0.
    labelled = []
    for t0, t1 in itertools.product(PERMS, repeat=2):
        f = tuple(t0[t1[q]] for q in range(5))
        orbit, q = set(), 0
        for _ in range(5):
            orbit.add(q)
            q = f[q]
        if len(orbit) == 5 and q == 0:
            labelled.append(tuple(zip(t0, t1)))
    rebuilt, count = reconstruct_pool()
    assert len(labelled) == count == 2880
    assert {rooted_canonical(t) for t in labelled} == set(rebuilt)
    assert rebuilt == [tuple(map(tuple, r['transitions'])) for r in result['pool']]
    for t in rebuilt:
        fixed_root = {relabel(t, (0,) + tail) for tail in itertools.permutations(range(1, 5))}
        assert len(fixed_root) == 24
        assert {rooted_canonical(s) for s in fixed_root} == {t}


def test_group_identity_all_starts_and_saved_invariants(result):
    assert U == A + B and V == B + C
    for row in result['pool']:
        t = tuple(map(tuple, row['transitions']))
        t0, p = (tuple(r[b] for r in t) for b in (0, 1))
        f = compose(t0, p)
        pinv = tuple(p.index(q) for q in range(5))
        # The unreduced word identity, then the order-five simplification.
        h = compose(power(f, 4), compose(pinv, compose(power(f, 5), compose(p, power(f, 2)))))
        assert compose(pinv, word_map(t, B)) == h == f
        assert word_map(t, U) == word_map(t, V) == compose(p, power(f, 13))
        assert not row['champion_separator'] and row['collision_pair'] is None
        for name, word in [('A', A), ('C', C), ('B', B), ('U', U), ('V', V)]:
            assert row['maps'][name] == [endpoint(t, word, q) for q in range(5)]
        assert semigroup(t)[0] == row['semigroup_size']


def test_collision_orbits_and_conjugacy(result):
    for row in result['rank4_champion']:
        t = tuple(map(tuple, row['transitions']))
        assert len({r[0] for r in t}) == 4 and len({r[1] for r in t}) == 5
        pairs = [pair for pair in itertools.combinations(range(5), 2) if t[pair[0]][0] == t[pair[1]][0]]
        assert pairs == [tuple(row['collision_pair'])]
        pair = pairs[0]
        observed = set()
        # Permutation orders in S5 divide 60; enough to see the whole orbit.
        for _ in range(60):
            observed.add(pair)
            pair = tuple(sorted(t[q][1] for q in pair))
        assert observed == set(map(tuple, row['collision_orbit']))
        assert min(relabel(t, p) for p in PERMS) == tuple(map(tuple, row['conjugacy_canonical']))
        assert endpoint(t, U) != endpoint(t, V)
        t0, p = (tuple(r[b] for r in t) for b in (0, 1))
        f = compose(t0, p)
        pinv = tuple(p.index(q) for q in range(5))
        e = power(f, 12)
        h = compose(power(f, 4), compose(pinv, compose(power(f, 5), compose(p, power(f, 2)))))
        assert compose(e, e) == e
        assert compose(p, h) == word_map(t, B)
        assert [q for q in range(5) if h[e[q]] != e[h[q]]] == row['separating_starts']
        for name, word in [('A', A), ('C', C), ('B', B)]:
            assert row['maps'][name] == [endpoint(t, word, q) for q in range(5)]


def test_counterexamples_and_csv(result):
    lookup = {r['id']: r for r in result['rank4_feature_counterexamples']}
    for trial in result['rank4_feature_search']:
        if trial['counterexample_ids']:
            yes, no = (lookup[i] for i in trial['counterexample_ids'])
            assert all(yes[f] == no[f] for f in trial['features'])
            assert endpoint(yes['transitions'], U) != endpoint(yes['transitions'], V)
            assert endpoint(no['transitions'], U) == endpoint(no['transitions'], V)
    with Path('results/v2_permutation_classification.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 172
    assert sum(r['scope'] == 'permutation_pool' for r in rows) == 120
    assert sum(r['champion_separator'] == 'True' for r in rows) == 52
    assert result['summary']['pool_champion_separators'] == 0


def test_v5_saved_conjugacy_and_semigroup_profiles(result):
    import re
    text = Path('results/v5_3_conjugacy.log').read_text()
    blocks = re.findall(r' indices: \[(\d+)\]\n T1 cycle type: (.*?)\n semigroup size: (\d+)\n rank profile: (.*?)\n canonical T: (.*)', text)
    import ast
    saved = {int(i): (ast.literal_eval(cycles), int(size), ast.literal_eval(profile), ast.literal_eval(t))
             for i, cycles, size, profile, t in blocks}
    assert len(saved) == 52
    for row in result['rank4_champion']:
        cycles, size, profile, t = saved[row['id']]
        assert cycles == tuple(row['t1_cycle_type'])
        assert size == row['semigroup_size']
        assert dict(profile) == {int(k): v for k, v in row['semigroup_rank_profile'].items()}
        assert t == tuple(map(tuple, row['conjugacy_canonical']))
        assert semigroup(row['transitions']) == (size, dict(profile))


def test_unpointed_invariants_cannot_characterize_membership(result):
    from analyze_v2_permutation_structure import unpointed_counterexample
    example = result['unpointed_counterexample']
    assert json.loads(json.dumps(unpointed_counterexample(result['rank4_champion']))) == example
    yes, no = (tuple(map(tuple, example[key])) for key in ('separating_table', 'nonseparating_table'))
    assert len(rooted_canonical(no)) == 5
    assert endpoint(yes, U) != endpoint(yes, V)
    assert endpoint(no, U) == endpoint(no, V)
    assert min(relabel(yes, p) for p in PERMS) == min(relabel(no, p) for p in PERMS)
    assert semigroup(yes) == semigroup(no)
