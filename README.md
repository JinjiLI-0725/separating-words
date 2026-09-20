# Separating Words — computational-note v1

A frozen computational study of binary words and finite deterministic
transition structures. The release documents reproduction of a known
length-48 obstruction, an exactly scored length-47 pair, and bounded witness
exchange experiments. We currently have an exact computational
near-identity/witness-exchange study, but no new theorem.

Start with [the release plan](notes/v1_release_plan.md) for the claim ledger,
reproduction commands, proposed note outline, artifact list, and release
blockers. This is preparation for v1.0; no release or DOI is declared here.

## Environment and quick verification

Run from the repository root on Linux. The audited environment uses CPython
3.10.12, NumPy 2.2.6 and pytest 9.1.1. There is no installable package metadata;
`PYTHONPATH` is required. A fresh dependency installation has not yet been
validated in an isolated environment.

```sh
python3.10 -m venv .venv
.venv/bin/python -m pip install numpy==2.2.6 pytest==9.1.1
PYTHONPATH=src .venv/bin/python scripts/count_dfas.py
PYTHONPATH=src .venv/bin/python scripts/verify_bkss_48.py
PYTHONPATH=src:scripts .venv/bin/python -m pytest -q
```

Expected counts for exactly 1,...,5 states are `1, 12, 216, 5248, 160675`
(total `166152`); the supplied length-48 pair has zero separators. The suite
has 23 tests, including exact champion/warm scores `52/64` and the V7
single-bit counterexample of score `74`. These are fixed checks, not word
searches. Archival SAT experiments require additional packages and are not
part of the core reproduction workflow.

## Meaning and limits

A score counts accessible binary transition tables, up to state relabeling
fixing start state 0, whose two runs end at different states. Accepting sets
are not counted. Removing unreachable states and canonically relabeling the
rest covers every pointed DFA on at most five states. Generator completeness
is checked against a separate labelled enumeration through three states;
both scalar and vectorized endpoint implementations share the direct generator.

The champion is `u=A B`, `v=B C`, where `A=(10)^12`, `C=(01)^12`, and
`B=10101101010101001010101`. Its 52 separators all have five states,
symbol ranks `(4,5)`, and symbol-0 indegrees `(0,1,1,1,2)` sorted by size.
Score 52 is the best observed score, with no global minimum claim.

See [V6](notes/v6_witness_exchange.md) for saved exchange observations and
[V7](notes/v7_structural_lemma.md) for the precise falsified implication.
V7 concerns eliminating the singular champion family; it does not resolve
the original permutation-to-singular implication. The 120-table pool covers
only the relevant permutation branch of the shared-block construction.

The BKSS attribution and the reported later length-48 optimality result need
primary-source bibliographic verification before publication. Neither result
is claimed as original here. Historical search commands in the V6 note are
provenance, not instructions for the frozen release. Do not run `run_search*`
or `search_*` entry points to reproduce the core claims.

License, citation metadata, an isolated reproduction transcript and final
release packaging remain outstanding; see the release plan before reuse or
archival publication.
