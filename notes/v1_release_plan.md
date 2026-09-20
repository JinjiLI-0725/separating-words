# Computational-note v1: release-readiness audit

Scope: freeze the results through `ffbfa90`, following V6 checkpoint
`c60d45e`. This audit changes documentation only. No V8, new candidate
search, optimality proof, or novelty claim is part of the release.

We currently have an exact computational near-identity/witness-exchange
study, but no new theorem.

## Minimum publication-safe claims

“Exact” below is relative to the explicit finite universe and implementation;
it is not a claim of a formally verified program or a new mathematical result.

| Category | Safe claim | Evidence and boundary |
| --- | --- | --- |
| Previously known mathematics | The length-48 BKSS pair is prior work; later length-48 optimality is reported in the supplied literature context. | Verify the primary publications and exact scope before citing either. This repository establishes no shortest-length result. |
| Reproduced enumeration | Accessible pointed binary transition structures up to relabeling number 1, 12, 216, 5,248, 160,675 for exactly 1–5 states; total 166,152. | `count_dfas.py`; direct restricted-growth generator; independent labelled enumerator comparison through k=3 only. These counts exclude choices of accepting sets. |
| Reproduced obstruction | The explicit distinct length-48 pair in `verify_bkss_48.py` has zero separating structures through five states, hence separation requires at least six states. | Scalar endpoint evaluation; no six-state upper bound is supplied by this script. This is an independent computational reproduction of a known obstruction, not an independently implemented five-state enumerator. |
| Exact computational observation | The recorded length-47 champion has exactly 52 separating structures; all are five-state. | `v4_3_witnesses.json`, V6 masks, regression tests; no separators with fewer states. “Champion” means best observed score, not optimum. |
| Exact witness structure | All 52 have symbol ranks `(4,5)`; sorted symbol-0 indegrees `(0,1,1,1,2)`. Their alternating 12th-power maps have rank 2 and are idempotent. | Full transition tables/traces in `v4_3_witnesses.json`; power profiles in `v6_power.json`. Scope is these tables only. |
| Exact finite observations | Square scores are 52, 74, 150, 64 at block flips `[]`, `[5]`, `[10]`, `[5,10]`; retained old counts 52, 0, 39, 0; introduced counts 0, 74, 111, 64. | `v6_1_exchange.structure.json`, rows and masks. Positions are zero-based. 36 new witnesses recur at all three non-champion corners; this does not imply a universal replacement family. |
| Exact finite reduction | The relevant permutation branch has 120 canonical tables, corresponding to 2,880 labelled tables. | `build_v6_permutation_pool.py` and saved pool. Both symbol maps permute five states and their `10` composition is a full 5-cycle. Not 120 permutations of a single map, nor 120 champion witnesses. |
| Exact finite certificate | Three witnesses cover the 58 score-≤200 rows of the 480-row V6.1 dataset; no two do. | Structure artifact: lower bound 3 plus a size-3 cover, despite `exact_minimum` being null. This is not a cover of every shared block. |
| Exact finite count with bounded follow-up | The selected three product constraints admit 190,860 blocks of length 23, including one equal-word case. | Independent forward recurrence in `audit_v6_results.py`; constraints and histogram saved in `v6_2_product_candidates.json`. Only 48 selected escapes were fully scored in V6.2 (49 rows including champion). |
| Heuristic/bounded observations | Search trajectories, best score 52, control comparisons, beam/SAT outcomes and selected product candidates. | Exact scores for evaluated pairs do not make candidate selection exhaustive. V6.1 includes all 277 radius-≤2 blocks, plus controls; the whole family of 2^23 blocks was not globally scored. |
| Falsified conjecture | In the radius-≤2 aligned family, eliminating all 52 champion witnesses need not introduce a singular witness. | Flip `[5]`: 0 retained, 52 eliminated, 74 introduced, all permutation witnesses. The warm corner also has no singular witnesses. |

The shared-block equation is **`u=A B`, `v=B C`**, not `v=C B`, with
`A=(10)^12`, `C=(01)^12`, `B=10101101010101001010101`.
Score is the number of canonical separating transition structures, not the
least number of separating states and not a count of labelled DFAs.

The elementary power argument in V6 is a mathematical proof: any map on at
most five states has idempotent 12th power unless it is a full 5-cycle.
All transient paths have length at most four and the other cycle lengths
divide 12. The exhaustive 3,413-map check is separate computational support.
No novelty is asserted for this fact or the permutation reduction.

## Literature and interpretation gates

Before publication, obtain the primary BKSS paper (Bulatov–Karpova–Shur–
Startsev, supplied as 2017) and reported Karpova–Shur work (supplied as 2021).
Confirm exact titles, author spelling, dates/versions, theorem numbers,
word conventions, length convention and whether the claimed optimality is
for binary identities of T5 in the sense used here. Record persistent source
identifiers and reconcile the script's pair with the printed identity.
No literature search was performed in this release-readiness audit.

Do not claim a new obstruction, a new shortest identity theorem, global
optimality of score 52, exhaustive length-47 coverage, or a universal
exchange law. V7 falsifies a singular-champion-to-singular-replacement
implication. It does **not** falsify the original permutation-to-singular
question, and it does not rule out every weakened statement. The V7 note
has been corrected to make that scope explicit without changing results.

## First-clone audit and reproducibility limits

- The README was empty; it now gives scope, setup and core verification.
  No `pyproject.toml`, requirements lock, CI, license, or citation metadata
  exists. Code imports require `PYTHONPATH`; commands require repository-root
  working directory. Use normal Python, not `python -O` (assertions matter).
- Observed environment: Linux, CPython 3.10.12, NumPy 2.2.6, pytest 9.1.1.
  NumPy and pytest suffice for core checks. The README pins these direct
  dependencies; transitive dependencies are not locked. Installation in a
  clean environment has not been tested. Archival SAT scripts use
  `python-sat` (observed 1.9.dev15); untracked Z3 code is outside the release.
- All currently tracked result JSON, JSONL, compressed JSON and NPZ files
  were readable in the audit. Exchange masks and row scores/retained/new
  counts were checked for consistency. This does not freshly rescore all
  529 saved rows. Result files and mathematical code were not changed.
- `audit_v6_results.py` primarily checks saved sets/metadata and independently
  recomputes the small product recurrence. `audit_v7_lemma.py` uses saved
  global masks and freshly evaluates the permutation pool. Neither is an
  independent full re-enumeration of all saved candidate scores.
- The V7 test freshly computes champion and mutant scores and the permutation
  count, but reads the zero-overlap assertion from JSON; it does not freshly
  compare champion/mutant masks. The scalar command below closes this core
  validation gap for a reproducer without changing code.
- Generator cross-validation covers k≤3. BKSS verification is an executable
  script rather than a pytest case; include its transcript in the archive.
  Witness rank/indegree/profile assertions are not all persistent pytest
  regressions. The additional read-only commands below check them explicitly.
- `analyze_v6_exchange.py` is a resumable experiment, not a release verifier.
  Its existing-summary fallback reads an ignored checkpoint eagerly; a
  pristine clone may fail when rerunning it. Do not use it for core release
  reproduction. The V6 historical product command used a 240-row snapshot;
  rerunning on all 480 rows can select different constraints. Reproduce the
  saved constraint histogram instead of selecting new candidates.
- `scripts/classify_B_tight.py` is tracked but belongs to another project:
  it imports unavailable `triangle_free` and needs absent graph data. Exclude
  it from the supported release workflow and decide its archival placement
  before tagging; no source file was removed during this documentation audit.

## Exact reproduction commands

Audit checks actually run: full suite **23 passed in 88.61 seconds**;
`count_dfas.py` reproduced all five counts; `verify_bkss_48.py` returned
zero separators among 166,152 structures. A read-only artifact check parsed
every tracked result container, compared V6 row/mask score and exchange
counts, checked all 52 saved rank/indegree profiles and compared the saved
permutation pool to regenerated tables. These checks ran within the
ten-minute computation budget. The extended scalar command and artifact
regeneration sequence below are reproduction instructions, not additional
claims that this audit reran them. No research search was run.

The five-state ordered-table fingerprint from this audit is
`9982601f70cbf4f4deeed5f748db76352fa8700a52d6980a990a5a4b184b5d75`.

Use a disposable clone/worktree at the release commit for commands marked
as regenerating artifacts. They overwrite results; timing fields and gzip
metadata are not expected to be byte-identical. No command below searches
for new word pairs. Setup is in README; from the repository root:

```sh
export PYTHONPATH=src:scripts
.venv/bin/python scripts/count_dfas.py
.venv/bin/python scripts/verify_bkss_48.py
.venv/bin/python -m pytest -q
```

Expected: the five counts above, zero BKSS separators, 23 tests passing.
`count_dfas.py` also prints ordered-table SHA-256 fingerprints; preserve
these with Python/package versions and commit ID in the release transcript.

Independent scalar endpoint comparison for the fixed champion, warm pair
and V7 mutant, including exact-set equality and witness structure (read-only):

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from collections import Counter
import numpy as np
from analyze_v6_exchange import A, B, C, U, V, WU, WV, scalar_verify, flip_many
from analyze_v6_structure import read
from analyze_v6_power import power
rows, masks = read(Path('results/v6_1_exchange'))
lookup = {(r['u'], r['v']): i for i, r in enumerate(rows)}
b = flip_many(B, [5])
pairs = [(U, V), (WU, WV), (A+b, b+C)]
sets = []
for pair, expected in zip(pairs, [52, 64, 74]):
    ids = scalar_verify(*pair)
    assert len(ids) == expected
    assert ids == np.flatnonzero(masks[lookup[pair]]).tolist()
    sets.append(set(ids))
assert not sets[0] & sets[1] and not sets[0] & sets[2]
data = json.loads(Path('results/v4_3_witnesses.json').read_text())
assert (data['u'], data['v']) == (U, V)
assert {5477+r['index_within_k'] for r in data['witnesses']} == sets[0]
for r in data['witnesses']:
    t = r['transitions']
    assert r['k'] == 5 and len(t) == 5
    assert [len({q[b] for q in t}) for b in (0, 1)] == [4, 5]
    assert sorted(Counter(q[0] for q in t).get(i, 0) for i in range(5)) == [0,1,1,1,2]
    for a, b in [(1,0), (0,1)]:
        f = power(tuple(t[t[q][a]][b] for q in range(5)), 12)
        assert len(set(f)) == 2 and power(f, 2) == f
print('Fixed-pair scalar scores, exact masks, and saved witness profiles agree.')
PY
```

For regeneration of fixed artifacts in the disposable copy:

```sh
.venv/bin/python scripts/analyze_v4_3_witnesses.py
.venv/bin/python scripts/build_v6_permutation_pool.py
.venv/bin/python scripts/analyze_v6_power.py
.venv/bin/python scripts/audit_v6_results.py
.venv/bin/python scripts/analyze_v6_structure.py results/v6_1_exchange
.venv/bin/python scripts/audit_v7_lemma.py
```

These reproduce the witness tables, pool, profiles, saved-data audit,
exchange-square/cover analysis and counterexample. They do not rescore
every V6 row. Full independent rescoring of the frozen rows and a standalone
five-state enumeration cross-check are stronger optional validation work,
not completed release-audit claims or instructions to resume search.

## Proposed 3–5 page computational note

1. **Context and scope (half page):** precise separation/identity definitions,
   cited known obstruction and optimality, computational reproduction goals.
2. **Enumeration and validation (three-quarters page):** accessible pointed
   tables, canonical discovery order, counts, endpoint criterion, scalar vs
   vectorized checks and the shared-generator limitation.
3. **The fixed length-47 pair (three-quarters page):** explicit A/B/C words,
   score and rank/indegree profiles; distinguish score from separation size.
4. **Finite witness exchange (one page):** four-corner table, old/new counts,
   permutation branch and finite-cover boundary; bounded controls as context.
5. **Falsification and reproducibility (half to one page):** exact V7
   implication/counterexample, limitations, artifact commands and availability.

Put full tables, masks, all 480/49 rows, product histograms and historical
search details in the repository supplement. Avoid claims of novelty in
title, abstract, conclusion and release metadata.

## GitHub v1.0 contents and Zenodo gates

The supported core must include:

- `README.md`, `.gitignore`, all three notes, `src/separating_words/*.py`
  and all six existing test files.
- Verification/analysis scripts: `count_dfas.py`, `verify_bkss_48.py`,
  `analyze_v4_3_witnesses.py`, `analyze_v5_2_structure.py`,
  `analyze_v5_3_conjugacy.py`, `analyze_v6_exchange.py`,
  `analyze_v6_structure.py`, `analyze_v6_power.py`,
  `build_v6_permutation_pool.py`, `audit_v6_results.py`, `audit_v7_lemma.py`.
- `search_v4_4_witness_guided.py` and `search_v6_product.py`: preserve these
  despite their names, because the verifiers import helper functions from
  them; importing does not run their guarded search entry points.
- All currently tracked result artifacts: `v4_1_fast_scored_neighbors.json`,
  `v4_2_batch_local.json`, `v4_3_witnesses.json`, `v4_4_witness_guided.json`,
  `v4_5_beam.json`, `v4_bkss_neighbors.json`, the two tracked V5 SAT results,
  V6.1/V6.2 JSONL + NPZ + gzip graphs + summaries, V6.1 structure,
  product candidates, audit, permutation pool, power profiles and V7 JSON.
  Older scalar/beam results are dependencies of the V6 audit, not disposable
  search debris. Preserve other tracked search scripts as historical source
  with no claim that rerunning them reproduces an identical trajectory.

Before tagging/depositing:

1. Verify literature and review all manuscript attributions and scope.
2. Obtain author/maintainer names, affiliations/ORCIDs as applicable, rights
   and explicit code/data licensing decisions; add LICENSE and CITATION.cff
   (and archive metadata as appropriate). Do not invent authors or licenses.
3. Finish the note PDF/source, document direct/transitive environment
   requirements and run the documented fixed checks in a clean clone.
   Save logs, versions, canonical fingerprints and an artifact checksum
   manifest. Existing tests are useful evidence, not a clean-install test.
4. Resolve the unrelated tracked graph script's place in the release.
   Preserve unrelated untracked files locally; do not bulk-add them.
5. Inspect an archive of the exact final Git commit, tag `v1.0` only after
   these gates, and confirm GitHub/Zenodo archive contents and metadata.
   Reserve/publish DOI through the owner's account, then insert the actual
   DOI in citation and release documentation. No DOI is reserved here.

Exclude `.venv`, caches, logs, runtime checkpoints, PID/backup files and the
five unrelated untracked files present at audit start. A Git tag archives
tracked files only; an indiscriminate filesystem upload would not.

This audit is release preparation, not authorization to publish or a claim
that all DOI gates have passed.
