#!/usr/bin/env python3
"""Read-only V1 audit and finite algebraic classification; never searches words.

Run from the repository root: PYTHONPATH=src .venv/bin/python
scripts/analyze_v2_permutation_structure.py. Only the two V2 result files are written.
Composition compose(f,g) means f after g; all tables are pointed at state 0.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from separating_words.canonical_generator import generate_canonical_dfas

U = '10101010101010101010101010101101010101001010101'
V = '10101101010101001010101010101010101010101010101'
A, B, C = '10' * 12, U[24:], '01' * 12
MUT_B = B[:5] + str(1 - int(B[5])) + B[6:]
WU = '10101010101010101010101010101001011101001010101'
WV = '10101001011101001010101010101010101010101010101'
PERMS = tuple(itertools.permutations(range(5)))


def compose(f, g):
    return tuple(f[q] for q in g)


def power(f, n):
    out = tuple(range(len(f)))
    for _ in range(n):
        out = compose(f, out)
    return out


def word_map(t, word):
    out = tuple(range(len(t)))
    for bit in word:
        out = tuple(t[q][int(bit)] for q in out)
    return out


def endpoint(t, word, start=0):
    for bit in word:
        start = t[start][int(bit)]
    return start


def relabel(t, p):
    out = [None] * len(t)
    for q, row in enumerate(t):
        out[p[q]] = tuple(p[r] for r in row)
    return tuple(out)


def rooted_canonical(t):
    # Independent BFS implementation; no import of V6 pool or canonicalize.
    order, labels = [0], {0: 0}
    for q in order:
        for r in t[q]:
            if r not in labels:
                labels[r] = len(order)
                order.append(r)
    return tuple(tuple(labels[r] for r in t[q]) for q in order)


def reconstruct_pool():
    """Choose f a 5-cycle and p arbitrary; solve T0=f p^-1, T1=p."""
    multiplicities = Counter()
    for tail in itertools.permutations(range(1, 5)):
        cycle = (0,) + tail
        f = [0] * 5
        for i, q in enumerate(cycle):
            f[q] = cycle[(i + 1) % 5]
        for p in PERMS:
            inverse = tuple(p.index(q) for q in range(5))
            t = tuple(zip(compose(f, inverse), p))
            canon = rooted_canonical(t)
            assert len(canon) == 5
            multiplicities[canon] += 1
    assert len(multiplicities) == 120
    assert set(multiplicities.values()) == {24}
    return sorted(multiplicities), sum(multiplicities.values())


def cycle_type(f):
    assert len(set(f)) == len(f)
    unseen, sizes = set(range(len(f))), []
    while unseen:
        q, length = min(unseen), 0
        while q in unseen:
            unseen.remove(q)
            length += 1
            q = f[q]
        sizes.append(length)
    return tuple(sorted(sizes))


def semigroup(t):
    generators = tuple(tuple(row[b] for row in t) for b in (0, 1))
    known, stack = set(generators), list(generators)
    while stack:
        f = stack.pop()
        for g in generators:
            h = compose(g, f)
            if h not in known:
                known.add(h)
                stack.append(h)
    return len(known), dict(sorted(Counter(len(set(f)) for f in known).items()))


def invariants(t, identifier, scope):
    t0, p = (tuple(r[b] for r in t) for b in (0, 1))
    kernel = sorted(tuple(q for q in range(5) if t0[q] == image) for image in set(t0))
    collision = next((cell for cell in kernel if len(cell) == 2), None) if len(set(t0)) == 4 else None
    orbit = []
    if collision:
        pair = collision
        while pair not in orbit:
            orbit.append(pair)
            pair = tuple(sorted(p[q] for q in pair))
    conjugates = [relabel(t, s) for s in PERMS]
    canonical = min(conjugates)
    size, profile = semigroup(t)
    maps = {name: word_map(t, word) for name, word in [('A', A), ('C', C), ('B', B), ('U', U), ('V', V)]}
    f = compose(t0, p)
    return dict(id=identifier, scope=scope, transitions=t, t1_cycle_type=cycle_type(p),
                t0_rank=len(set(t0)), t0_indegrees=sorted(t0.count(q) for q in range(5)),
                t0_kernel=kernel, t0_kernel_sizes=sorted(map(len, kernel)),
                collision_pair=collision, collision_orbit=orbit, collision_orbit_size=len(orbit),
                conjugacy_canonical=canonical, automorphism_count=sum(s == t for s in conjugates),
                semigroup_size=size, semigroup_rank_profile=profile,
                maps=maps, endpoints={key: value[0] for key, value in maps.items()},
                block_ranks={key: len(set(value)) for key, value in maps.items()},
                block_idempotent={key: compose(value, value) == value for key, value in maps.items()},
                b_equals_p_f=maps['B'] == compose(p, f),
                separating_starts=[q for q in range(5) if maps['U'][q] != maps['V'][q]],
                champion_separator=maps['U'][0] != maps['V'][0])


def feature_search(rows, fields):
    """Test every subset, not a trained accuracy score; retain explicit conflicts."""
    out = []
    encoded = [{name: json.dumps(row[name], sort_keys=True) for name in fields} for row in rows]
    for width in range(1, len(fields) + 1):
        for names in itertools.combinations(fields, width):
            buckets = defaultdict(list)
            for row, codes in zip(rows, encoded):
                key = tuple(codes[name] for name in names)
                buckets[key].append(row)
            conflicts = [group for group in buckets.values() if len({r['champion_separator'] for r in group}) > 1]
            example = None
            if conflicts:
                group = conflicts[0]
                example = [next(r['id'] for r in group if r['champion_separator']),
                           next(r['id'] for r in group if not r['champion_separator'])]
            out.append(dict(features=names, exact=not conflicts, conflicting_buckets=len(conflicts), counterexample_ids=example))
    return out


def unpointed_counterexample(champion_rows):
    """An accessible re-rooting defeats even complete unpointed conjugacy."""
    for row in champion_rows:
        t = tuple(map(tuple, row['transitions']))
        for q in range(1, 5):
            swap = list(range(5))
            swap[0], swap[q] = q, 0
            other = rooted_canonical(relabel(t, swap))
            if len(other) == 5 and endpoint(other, U) == endpoint(other, V):
                assert min(relabel(other, p) for p in PERMS) == min(relabel(t, p) for p in PERMS)
                return dict(champion_id=row['id'], reroot_at=q,
                            separating_table=t, nonseparating_table=other,
                            separating_endpoints=[endpoint(t, U), endpoint(t, V)],
                            nonseparating_endpoints=[endpoint(other, U), endpoint(other, V)],
                            implication='No function of unpointed simultaneous-conjugacy invariants alone characterizes pointed champion separation.')
    raise AssertionError('Expected an accessible nonseparating re-rooting')


def main():
    assert U == A + B and V == B + C and len(U) == len(V) == 47
    pool, labelled = reconstruct_pool()
    saved_pool = json.loads(Path('results/v6_permutation_pool.json').read_text())
    assert pool == [tuple(map(tuple, t)) for t in saved_pool['transitions']]
    assert (saved_pool['count'], saved_pool['labeled_count']) == (120, labelled)
    print('Reconstructed and checked 120-table pool.', flush=True)
    words = [U, V, A + MUT_B, MUT_B + C, WU, WV]
    witness_ids = [[], [], []]
    tables, counts, rank4_controls = {}, {}, []
    pool_ids = {}
    pool_set = set(pool)
    idx = 0
    for k in range(1, 6):
        count = 0
        for t in generate_canonical_dfas(k):
            ends = [endpoint(t, w) for w in words]
            hit = ends[0] != ends[1]
            for j in range(3):
                if ends[2*j] != ends[2*j+1]:
                    witness_ids[j].append(idx)
                    tables[idx] = t
            if t in pool_set:
                pool_ids[t] = idx
            t0, t1 = (tuple(r[b] for r in t) for b in (0, 1))
            if k == 5 and len(set(t0)) == 4 and len(set(t1)) == 5:
                a, c, b = (word_map(t, w) for w in (A, C, B))
                pair = tuple(q for q in range(5) if t0.count(t0[q]) == 2)
                orbit, current = [], pair
                while current not in orbit:
                    orbit.append(current)
                    current = tuple(sorted(t1[q] for q in current))
                rank4_controls.append(dict(id=idx, champion_separator=hit,
                    t1_cycle_type=cycle_type(t1), collision_orbit_size=len(orbit),
                    a_rank=len(set(a)), c_rank=len(set(c)), b_rank=len(set(b)),
                    a_fixes_start=a[0] == 0, c_fixes_b_start=c[b[0]] == b[0],
                    transitions=t))
            count += 1
            idx += 1
        counts[k] = count
        print(f'Checked {count} tables on {k} states.', flush=True)
    assert list(counts.values()) == [1, 12, 216, 5248, 160675]
    old, changed, warm = map(set, witness_ids)
    assert (len(old), len(changed), len(warm), len(old & changed), len(old & warm)) == (52, 74, 64, 0, 0)
    assert len(pool_ids) == 120 and old.isdisjoint(pool_ids.values())
    assert changed <= set(pool_ids.values()) and warm <= set(pool_ids.values())
    assert all(len(tables[i]) == 5 and len({r[0] for r in tables[i]}) == 4
               and len({r[1] for r in tables[i]}) == 5 for i in old)
    audit = dict(canonical_counts=counts, total=idx, champion_ids=sorted(old),
                 mutation_ids=sorted(changed), warm_ids=sorted(warm), pool_global_ids=sorted(pool_ids.values()))
    # Compare saved transition data and exact sets, not only their scalar summaries.
    sat = json.loads(Path('results/v5_5_witness_sat.json').read_text())
    assert sat['seed_u'] == U and sat['seed_v'] == V and set(sat['witness_indices']) == old
    v5log = Path('results/v5_3_conjugacy.log').read_text()
    import re
    assert {int(i) for i in re.findall(r'indices: \[(\d+)\]', v5log)} == old
    saved_power = json.loads(Path('results/v6_power.json').read_text())
    assert set(map(int, saved_power['profiles'])) == old | warm
    for key, saved in saved_power['profiles'].items():
        t = tables[int(key)]
        assert tuple(map(tuple, saved['transitions'])) == t
        for block in ('10', '01'):
            f = word_map(t, block * 12)
            assert list(f) == saved['image_' + block + '_12']
            assert len(set(f)) == saved['rank_' + block + '_12']
            assert (compose(f, f) == f) == saved['idempotent_' + block + '_12']
        assert saved['symbol_ranks'] == [len({r[b] for r in t}) for b in (0, 1)]
    for name in ('v6_1_exchange', 'v6_2_exchange'):
        rows = [json.loads(s) for s in Path('results/' + name + '.jsonl').read_text().splitlines()]
        with np.load('results/' + name + '.sets.npz') as data:
            masks = np.unpackbits(data['packed'], axis=1, count=idx).astype(bool)
        assert len(rows) == len(masks)
        exact_checks = 0
        for row, mask in zip(rows, masks):
            ids = set(np.flatnonzero(mask).tolist())
            assert row['score'] == len(ids) and row['retained'] == len(ids & old)
            assert row['introduced'] == len(ids - old)
            for j in range(3):
                if (row['u'], row['v']) == tuple(words[2*j:2*j+2]):
                    assert ids == set(witness_ids[j])
                    exact_checks += 1
        audit[name] = dict(rows=len(rows), exact_fixed_pair_checks=exact_checks,
                           all_saved_score_and_overlap_checks=True)
    v7 = json.loads(Path('results/v7_lemma_falsification.json').read_text())
    assert v7['scope']['mutation']['u'] == words[2] and v7['scope']['mutation']['v'] == words[3]
    for key, value in dict(old_score=52, mutation_score=74, old_retained=0, eliminated_old=52,
                           introduced=74, permutation_pool_count=74, rank_deficient_replacements=0).items():
        assert v7[key] == value
    audit['v7_recomputed'] = True
    print('Saved-data audits passed; computing invariants.', flush=True)
    pool_rows = [invariants(t, i, 'permutation_pool') for i, t in enumerate(pool)]
    for row in pool_rows:
        row['global_id'] = pool_ids[tuple(map(tuple, row['transitions']))]
        assert row['t0_rank'] == 5 and row['collision_pair'] is None
        assert row['b_equals_p_f'] and not row['separating_starts']
    champion_rows = [invariants(tables[i], i, 'rank4_champion') for i in sorted(old)]
    assert all(r['t0_indegrees'] == [0, 1, 1, 1, 2] for r in champion_rows)
    print(f'Checking 127 feature subsets on {len(rank4_controls)} rank-4 tables.', flush=True)
    searches = feature_search(rank4_controls, ['t1_cycle_type', 'collision_orbit_size', 'a_rank', 'c_rank', 'b_rank', 'a_fixes_start', 'c_fixes_b_start'])
    conflict_ids = {i for r in searches if r['counterexample_ids'] for i in r['counterexample_ids']}
    conflicts = [r for r in rank4_controls if r['id'] in conflict_ids]
    summary = dict(pool_count=120, labelled_count=labelled, labelled_per_rooted_table=24,
                   pool_champion_separators=0, champion_separators=52, mutation_separators=74,
                   warm_separators=64, rank4_permutation_universe=len(rank4_controls),
                   pool_unpointed_conjugacy_classes=len({tuple(map(tuple, r['conjugacy_canonical'])) for r in pool_rows}),
                   champion_unpointed_conjugacy_classes=len({tuple(map(tuple, r['conjugacy_canonical'])) for r in champion_rows}),
                   pool_semigroup_sizes=dict(Counter(r['semigroup_size'] for r in pool_rows)),
                   champion_semigroup_profiles=len({json.dumps(r['semigroup_rank_profile'], sort_keys=True) for r in champion_rows}),
                   rank4_exact_feature_subsets=sum(r['exact'] for r in searches))
    sources = ['scripts/build_v6_permutation_pool.py', 'scripts/analyze_v5_2_structure.py',
               'scripts/analyze_v5_3_conjugacy.py', 'scripts/analyze_v6_power.py', 'scripts/audit_v7_lemma.py',
               'results/v5_2_structure.log', 'results/v5_3_conjugacy.log', 'results/v5_5_witness_sat.json',
               'results/v6_power.json', 'results/v6_permutation_pool.json', 'results/v7_lemma_falsification.json']
    sources += ['results/' + name + suffix for name in ('v6_1_exchange', 'v6_2_exchange') for suffix in ('.jsonl', '.sets.npz')]
    result = dict(schema_version=1, words=dict(U=U, V=V, A=A, B=B, C=C, mutation_B=MUT_B),
                  composition='compose(f,g) = f after g; start state 0', summary=summary, audit=audit,
                  source_sha256={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
                  pool=pool_rows, rank4_champion=champion_rows,
                  characterization=dict(scope='120-table permutation pool', predicate='False',
                     falsification_checked=120, counterexamples=[],
                     algebra='f=T0*T1, p=T1, f^5=id; p^-1*B=f^4*p^-1*f^5*p*f^2=f; B=p*f; U=V=p*f^13'),
                  rank4_feature_search=searches, rank4_feature_counterexamples=conflicts,
                  unpointed_counterexample=unpointed_counterexample(champion_rows))
    Path('results/v2_permutation_classification.json').write_text(json.dumps(result, indent=2) + '\n')
    fields = list(pool_rows[0])
    with Path('results/v2_permutation_classification.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in pool_rows + champion_rows:
            writer.writerow({k: json.dumps(v, separators=(',', ':')) if isinstance(v, (tuple, list, dict)) else v for k, v in row.items()})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
