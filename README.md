# Separating Words — computational-note v1.0.0

A frozen computational study of binary words and finite deterministic
transition structures. The release documents reproduction of a known
length-48 obstruction, an exactly scored length-47 pair, and bounded witness
exchange experiments. We currently have an exact computational
near-identity/witness-exchange study, but no new theorem.

Start with [the release plan](notes/v1_release_plan.md) for the claim ledger,
reproduction commands, proposed note outline, artifact list, and release
blockers. The intended release is **v1.0.0**; it has not been published here,
and a Zenodo DOI is not yet assigned.

## Environment and quick verification

Run from the repository root on Linux. The audited environment uses CPython
3.10.12, NumPy 2.2.6 and pytest 9.1.1. There is no installable package metadata;
`PYTHONPATH` is required. Fresh dependency installation and the core
reproduction checks succeeded in a completely fresh GitHub clone at commit
`04406e1`, using the versions above.

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

The clean-clone audit reproduced all five counts (total 166,152), zero BKSS
separators and **23 passing tests**. The k=5 ordered enumeration SHA-256 was
`9982601f70cbf4f4deeed5f748db76352fa8700a52d6980a990a5a4b184b5d75`.
V6.1 and V6.2 audits both reported best score 52; the independent product
check total was 190,860. The V7 audit reproduced old score 52, mutation score
74, zero old witnesses retained, 74 introduced, 74 permutation-pool witnesses
and zero rank-deficient replacements, confirming the tested implication's
falsification. See the release plan for the audit's scope and limitations.

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

Primary-source verification of the bibliographic information and theorem
statement is complete. Bulatov, Karpova, Shur and Startsev (2017) constructed
the length-48 T5 identity and conjectured optimality. Karpova and Shur (2021),
*Journal of Automata, Languages and Combinatorics* 26(1–2), 67–89, state that
they prove the shortest identity in T5 has length 48. We have not independently
checked the full 2021 proof. Neither result is claimed as original here.
Historical search commands in the V6 note are
provenance, not instructions for the frozen release. Do not run `run_search*`
or `search_*` entry points to reproduce the core claims.

## License, citation and final packaging

The repository's original software/code is licensed under the
[MIT License](LICENSE), copyright (c) 2026 Jinji Li. This does not relicense
third-party papers, cited literature or other third-party material; their
respective rights and licenses remain applicable.

[CITATION.cff](CITATION.cff) supplies citation metadata for the intended
software/research artifact version 1.0.0, with release date 2026-09-20.
No DOI is included; a Zenodo DOI will be added after assignment.

The manuscript source remains [paper/paper_v1.tex](paper/paper_v1.tex).
Before tagging v1.0.0, compile it and visually inspect the final PDF.
No LaTeX compiler is available in the preparation environment, so PDF
compilation and visual inspection remain outstanding. Final packaging must
also archive the completed clean-clone reproduction evidence; see the
release plan for the remaining steps.
