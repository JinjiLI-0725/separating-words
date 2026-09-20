# V6 witness exchange

## Prior work inspected

Before editing, inspected the empty `notes/` directory, git history through
`9f6b2fc`, the canonical generator and verifier, tests, and V4.3, V4.4,
V4.5, V5.2, V5.3, and V5.5 scripts/results. Baseline: 15 tests passed.
V4.1 already scored 2,116 deletion pairs; V4.2 scored 2,304 local pairs;
V4.4 tested 17,550 candidates on W0 but globally scored only 100 finalists;
V4.5 completed 12 generations with best 52. V5.2 found 51 coarse structural
families, V5.3 found 52 conjugacy classes, and V5.5 timed out. No SAT word
search or state-relabeling clustering was repeated.

Prior exact witness sets from the saved V4.5 beam are reused. Previously
scored pairs lacking saved sets are evaluated to recover *new exchange data*,
not presented as newly discovered candidates. The 52/64 regression checks
are deliberate re-verification. Existing unrelated untracked files are left
untouched.

## Reproduction and artifacts

From the repository root:

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v6_exchange.py
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v6_structure.py results/v6_1_exchange
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v6_power.py
PYTHONPATH=src:scripts .venv/bin/python scripts/search_v6_product.py results/v6_1_exchange
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v6_exchange.py --prefix results/v6_2_exchange --candidates results/v6_2_product_candidates.json --seconds 300
```

The product experiment actually used the explicitly recorded 240-row
checkpoint; using the completed first dataset can choose a different cover.
The saved product candidate file reproduces the exact scored follow-up.
The default first-run budget is 900 seconds, checked after each 24-pair batch;
rerun to resume if incomplete. Summarization and loading add overhead. No
established scorer or generator is modified.

- `.jsonl`: words, zero-based mutations, score, retained/eliminated/introduced
  counts, intersection/union/Jaccard against W0, state-size counts, endpoint
  patterns when freshly evaluated, and exact-set provenance.
- `.sets.npz`: packed Boolean candidate-by-DFA incidence matrix. Decode with
  `np.unpackbits(archive['packed'], axis=1, count=166152)` (default big bit order).
- `.graph.json.gz` (gzip-compressed JSON): witness families grouped by identical incidence columns,
  with candidate -> eliminated-old / introduced-new family edges.
- `.summary.json`: family summaries, recurring identical new sets, low-score
  incidence families, and a greedy finite-family witness cover.
- `.structure.json`: the four-corner exchange square, Pareto frontier, and
  low-score cover bounds. A cover certifies only this finite dataset.
- `v6_power.json`: all 116 champion/warm witness tables and power profiles,
  plus exhaustive checks on every map on at most five states.
- `v6_2_product_candidates.json`: exact DP counts by Hamming distance,
  selected constraints, tables, source snapshot, and emitted candidates.

DFA IDs are zero-based concatenations of canonical generator order for
k=1,...,5. State-count boundaries are 0, 1, 13, 229, 5477, 166152. A "witness"
here is a transition structure; final states can be selected to separate
unequal endpoints. No accepting-state subsets are enumerated.

## Exact block identity and the 52-to-64 square

Write

```
A = (10)^12
B = 10101101010101001010101
C = (01)^12
u = A B
v = B C
```

A +24 aligned mutation is precisely a mutation of the same B in both words.
The four corners obtained by flipping shared-block positions 5 and 10 are:

| Positions flipped in B | Score | Old retained | New introduced |
|---|---:|---:|---:|
| none | 52 | 52 | 0 |
| 5 | 74 | 0 | 74 |
| 10 | 150 | 39 | 111 |
| 5,10 | 64 | 0 | 64 |

The 74->64 edge eliminates 33 witnesses and introduces 23; the 150->64 edge
eliminates 95 and introduces 9. Of the new witnesses, 36 occur at all three
non-champion corners. There are nine nonempty incidence cells across the
square. These are reversible exchange edges, not monotone progress toward
zero. Exact membership is stored in the structure JSON.

## Structural distinction behind the exchange

All 52 W0 witnesses have symbol-map ranks (4,5). The maps induced by A and C
are idempotent and both have rank 2. All 64 warm-pair witnesses instead have
symbol-map ranks (5,5); their two-symbol alternating maps are full 5-cycles,
so A and C remain rank-5 permutations and are not idempotent.

Elementary lemma: for any map f on at most five states, f^12 is idempotent
unless f is a full 5-cycle. Every orbit reaches a cycle within four steps.
If there is no 5-cycle, all cycle lengths belong to {1,2,3,4}, hence divide
12; advancing by another 12 fixes every point in the image of f^12. A
5-cycle uses every state and f^12 = f^2 is not idempotent. In particular,
if either binary symbol map is singular, both two-symbol compositions have
idempotent 12th powers. Exhaustive checks cover 3,413 maps, with exactly 24
exceptions, all five-cycles.

This explains a useful algebraic division induced by the +24 construction.
It does **not** show that every length-47 pair, or every shared B, must have
a separator. The rank restrictions above are observations about these two
specific exact witness sets.

## Adaptive product follow-up

The first 240 rows require at least three witnesses to cover their score<=200
subset (no two incidence columns cover it; a greedy three-column cover does).
Chosen global IDs: 79962, 33525, 6022. The first is a permutation witness;
the second is an original rank-(4,5) witness. The third adds another singular
obstruction. The DP tracks two runs per DFA: start states after A and after
the empty word; its terminal condition applies C to the second endpoint.
It counts all 2^23 blocks, stratified by Hamming distance from B.

The DP found 190,860 blocks evading all three constraints. This includes the
unique block producing identical words, B=(10)^11 1, which is excluded from
candidate emission. Thus there are 190,859 nontrivial block escapes: the
three-witness sample cover is not a universal obstruction. The 48 emitted
new candidates all have distance 3. Previously scored pairs and the complete
planned V6.1 family are excluded from emission. Product DP took 4.018 s;
loading constraints plus candidate generation took 15.481 s.

The follow-up deliberately samples 48 of the 59 distance-three escapes;
it is not an exhaustive global search over shared blocks.

## Complete permutation branch

`build_v6_permutation_pool.py` constructs `v6_permutation_pool.json`, the
complete 120-table permutation obstruction pool for **any** shared B. For
permutations, the two-letter maps f=T0 o T1 and g=T1 o T0 are conjugate. If
f is not a 5-cycle, both 12th powers are identities, so both words simply
finish at T_B(0). Such a DFA cannot separate the aligned family.

For the exceptional branch there are 24 choices for a 5-cycle f and 120
choices for T1, uniquely determining T0: 2,880 labeled tables. Every table
is accessible because f itself is transitive. Quotienting by the 24 state
relabelings fixing the start gives 120 canonical tables; explicit canonical
construction verifies this count. This is a reduction of the permutation
branch, not a replacement for the exhaustive verifier. Singular transition
maps still require separate constraints.

The product's three representatives have these useful block maps (images
listed in state order 0,...,4):

| Witness ID | A map | C map |
|---|---|---|
| 79962 | 1,2,4,0,3 | 4,0,3,1,2 |
| 33525 | 4,3,4,3,4 | 3,4,3,3,4 |
| 6022 | 0,0,0,0,0 | 1,1,1,1,1 |

Thus the third constraint is simply T_B(0)=1 in its DFA; the first enforces
one permutation condition, and the second compares runs through rank-2
projections. The product needed only 590 distinct joint transition states.
