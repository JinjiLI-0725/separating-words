# V2: permutation pool versus rank-4 champion witnesses

**VERIFIED FACT.** These are two different branches. The V6 120-table pool
has both letters invertible, hence rank(T0)=5, singleton kernel blocks, and
no collision pair. The champion's 52 separators all have ranks (4,5).
Their intersection with the pool is empty. There cannot be a nonempty
52-of-120 classification of this champion. This is a scope correction,
not a contradiction of either saved V1 fact.

All statements here concern transition structures with distinguished start
state 0, without accepting sets. The existing branch `v2-permutation-structure`
was reused. V1 artifacts and tag `v1.0.0` are preserved.

**VERIFIED FACT: pool size and quotient.** Put p=T1 and f=T0∘T1. There are
(5−1)!=24 labelled 5-cycles f and 5!=120 choices of p. Each determines the
unique T0=f∘p⁻¹, giving 2,880 labelled tables. The presence of f makes every
state reachable from 0. Relabellings fixing 0 form S4, of size 24, and act
freely: an automorphism fixing 0 fixes every state reached by a word.
Consequently the pointed quotient has 2,880/24=120 tables. Dividing by 120
would incorrectly forget the distinguished start state. Unpointed
simultaneous conjugacy is recorded separately in the JSON.

The new reconstruction chooses f and p, solves for T0, and uses its own BFS
canonicalizer. It agrees table-for-table with the saved V6 pool. A separate
test enumerates all 120² pairs of permutations and selects the five-cycle
products. No existing V6 pool-builder function is used for reconstruction.

**VERIFIED FACT: exact algebraic exclusion of the entire pool.** Composition
acts right to left. Let b be the map of the shared block
`B=10101101010101001010101`, which is the suffix of U and prefix of V.
The words are U=(10)^12 B and V=B (01)^12, both of length 47.
For any invertible p=T1 (T0 need not be invertible), substitute
T0=f∘p⁻¹ into B and cancel adjacent p⁻¹p to obtain

```
h = p⁻¹∘b = f⁴∘p⁻¹∘f⁵∘p∘f².
U = p∘h∘f¹²,             V = p∘f¹²∘h.
```

In the pool f⁵=id, so h=f⁶=f and b=p∘f. Both champion maps are
p∘f¹³=p∘f³. Thus **no starting state** of any pool table separates them.
The exact membership predicate on all 120 tables is `False`; exhaustive
falsification finds zero counterexamples, checking all five starting states.
This conclusion has an explicit algebraic derivation, not just a correlation.
Outside this pool, when both letters permute at most five states, a product
that is not a 5-cycle has order dividing 12. Both alternating block maps are
then identities. Hence the champion is an identity on the whole permutation
branch on at most five states.

**VERIFIED FACT: useful rank-4 reduction.** For rank(T0)=4 and invertible p,
f is singular. Every cycle length is at most 4, and every transient path has
length at most 4. Therefore e=f¹² is idempotent. The exact pointed separation
criterion is

```
h(e(0)) != e(h(0)),     h=f⁴∘p⁻¹∘f⁵∘p∘f².
```

This follows by cancellation of the outer bijection p. It is a shorter
algebraic decision criterion, not a classification by coarse invariants.
The recorded full maps of A, C and B also give the exact universal criterion
b(A(0)) != C(b(0)). State-labelled maps and kernel blocks are equivariant
under relabelling; their ranks, sizes, and canonical simultaneous-conjugacy
representatives are invariants. Endpoint comparisons require the pointed
start, so unpointed conjugacy alone must not be treated as pointed membership.

**VERIFIED FACT: audit scope.** The script enumerates all 166,152 canonical
accessible tables on at most five states (counts 1, 12, 216, 5,248, 160,675).
It evaluates only the three fixed existing pairs: champion, warm64 and V7's
position-5 shared-block mutation. This is not a word search. It compares the
champion IDs to V5.5's saved witness list and V5.3's logged class IDs, checks
all 116 saved V6 power-profile transition tables and their block maps, and
checks all saved V6.1/V6.2 mask scores and overlaps. For the three fixed pairs
present in those files it compares full witness sets to fresh evaluation.
It does not re-evaluate all other V6 candidate words, rerun SAT, or rerun the
historical product-language search. Source SHA-256 hashes record exactly
which artifacts were inspected.

**COUNTEREXAMPLE: V7 reproduced.** Flip zero-based position 5 of B. The changed
pair has exactly 74 separators, all in the permutation pool, and retains
zero of the 52 champion separators. Thus eliminating all singular champion
witnesses does not force a singular replacement. This is the saved V7
counterexample, independently re-evaluated, not a newly discovered example.
The warm pair has 64 separators, also entirely in the pool, and shares zero
champion witnesses.

**EMPIRICAL PATTERN.** All 52 rank-4 champion witnesses have rank-2 idempotent
maps for both alternating blocks. This is an exact finite observation; by
itself it is not a sufficient membership criterion. The feature experiment
checks every nonempty subset of seven explicitly chosen features across the
entire accessible five-state rank-4/T1-permutation universe: T1 cycle type,
collision-pair orbit size, ranks of A/C/B, A fixing 0, and C fixing b(0).
Each failed feature combination stores concrete opposite-label tables with
identical feature values. This experiment does not exhaust every possible
small algebraic predicate.

**CONJECTURE.** No new general conjecture is asserted. In particular, this
work does not infer rank-4 sufficiency from the champion's observed profile.

The next mathematically justified experiment is to study e=f¹² and
h=f⁴p⁻¹f⁵pf² on the rank-4 branch, particularly the two-point image of e:
classify the pointed failure of he=eh and which additional kernel/image
incidence data distinguish the stored opposite-label examples. Enumerate
transition structures and induced maps, keeping the words fixed. This targets
the actual surviving singular branch and does not require word or SAT search.

**V2 continuation: exact e/h audit.** The standalone script
`scripts/analyze_v2_rank4_eh.py` enumerates the complete 4,082-table
rank-4/T1-permutation universe. It confirms e²=e for every table and the
pointed identity
`U(0) != V(0) iff h(e(0)) != e(h(0))`. The image rank of e is 1, 2, 3,
or 4 on 461, 829, 1,196, or 1,596 tables respectively. All 52 champion
witnesses lie in the rank-2 image slice. This is a structural localization,
not a claim that rank(e)=2 is sufficient: the saved certificate still uses
the start state's incidence with e and h.

Reproduce the continuation with:

```sh
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v2_rank4_eh.py
PYTHONPATH=src:scripts .venv/bin/python -m pytest -q
```

The continuation regression is `tests/test_v2_rank4_eh.py`; the V2 test
subset currently passes 7 tests, and the repository collects 30 tests total.

Reproduction (repository root):

```sh
PYTHONPATH=src .venv/bin/python scripts/analyze_v2_permutation_structure.py
PYTHONPATH=src:scripts .venv/bin/python -m pytest -q
```

The JSON contains all 120 pool records and, separately, all 52 champion
records, audit evidence, feature trials, and counterexample tables. The CSV
contains the same 172 classified records with an explicit `scope` column;
IDs in the pool are sorted pool indices, while champion IDs are global
canonical-generator indices. `global_id` disambiguates pool records.
Missing collision pairs are JSON null (empty cells in CSV), never invented
rank-4 data for permutation tables.

**VERIFIED FACT: exact classification counts.** The pool comprises 28
unpointed simultaneous-conjugacy classes. Its generated semigroups are groups:

| Semigroup size | Pointed pool tables |
| --- | ---: |
| 5 | 5 |
| 10 | 5 |
| 20 | 10 |
| 60 | 50 |
| 120 | 50 |

The 52 champion witnesses comprise 52 unpointed conjugacy classes and 34
semigroup rank profiles. Their collision-pair orbit sizes are 2 (14 tables),
3 (10), 4 (8), 5 (12), and 6 (8). All have rank(B)=2. On 26 witnesses
rank(U)=1 and rank(V)=2; on the other 26 both ranks are 2. These are finite
counts, not sufficient characterizations. The complete rank-4/T1-permutation
control universe contains 4,082 accessible pointed tables. None of the 127
feature subsets is exact; even the seven-feature tuple has eight buckets
containing both labels. The mask audit checks 480 V6.1 rows and 49 V6.2 rows,
with respectively three and one freshly re-evaluated fixed pairs present.

**COUNTEREXAMPLE: all seven coarse features fail together.** Global table
59,797 separates, whereas 8,172 does not:

```
59797: ((1,1), (2,3), (1,4), (3,2), (4,0))
 8172: ((0,1), (1,2), (2,3), (1,4), (4,0))
```

Both have T1 cycle type (5), collision orbit size 5, ranks(A,C,B)=(2,2,2),
A(0)≠0, and C(b(0))=b(0). Thus every subset of these seven features also
fails, independently of how a lookup rule on feature values is chosen.

**COUNTEREXAMPLE: no unpointed invariant combination can suffice.** A stronger
obstruction uses global champion table 55,596 and an accessible re-rooting
at its state 1:

```
Separating:    ((1,1), (2,2), (3,0), (4,3), (3,4)); endpoints (3,4)
Nonseparating: ((1,1), (2,3), (4,2), (0,0), (2,4)); endpoints (2,2)
```

These tables are simultaneously conjugate after forgetting the start state.
Both are accessible from their displayed state 0. Consequently they agree
on *every* unpointed conjugacy invariant, including the entire generated
semigroup up to conjugation and the collision-pair orbit structure. They
have different pointed membership. This rules out any characterization
using only such invariants, not just the seven tested features. An exact
nontrivial rank-4 classification must retain information about the start's
position relative to the kernel/image maps. The `he(0) != eh(0)` criterion
above does so, but a smaller structural characterization remains open.

Validation: all 23 existing tests and all six new V2 tests pass (29 total).
The new tests also compare all saved V5.3 canonical representatives and
semigroup profiles to recomputed values. V5.5's archived timeout is used
only as a witness-list source; no conclusion is drawn from its search status.
