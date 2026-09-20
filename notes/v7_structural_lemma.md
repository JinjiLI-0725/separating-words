# V7 structural-lemma audit

This bounded session asks whether the V5/V6 exchange effect can be expressed as
an implication from removing the champion witness family to the appearance of a
rank-deficient replacement family. The scope is the exact V6.1 aligned family:

\[
 u=A B' ,\qquad v=B' C,
 \quad A=(10)^{12},\ C=(01)^{12},
\]

where `B'` ranges over the complete degree-at-most-two bit flips of the saved
23-bit block `B`. Scores are exact over all 166,152 canonical DFAs on at most
five states. “Permutation” means membership in the complete 120-table
canonical pool (the quotient of 2,880 labelled pairs in which both symbols are
permutations and the `10` composition is a 5-cycle). It is a classification of
the separator transition tables, not a claim about accepting subsets.

## Audited V6 facts

The saved champion has score 52, all on five states, with every witness having
symbol-map ranks `(4,5)`. The warm pair has score 64, is disjoint from the old
52-witness set, and all 64 witnesses have symbol-map ranks `(5,5)`; its relevant
two-symbol maps are full 5-cycles. The four-corner shared-block square at flip
positions `[]`, `[5]`, `[10]`, `[5,10]` has scores `52, 74, 150, 64`. The
`[5]` corner retains zero old witnesses and introduces 74; the `[5,10]` corner
retains zero and introduces 64. The independent audit reproduces the exact
product-DP escape histogram (190,860 blocks, one equal-word block excluded from
the 190,859 nontrivial escapes). The permutation pool has 120 canonical tables,
representing 2,880 labelled tables; it is complete for the permutation branch,
not for singular maps or for all length-47 pairs.

## Candidate lemma and falsification

The strongest simple statement suggested by the exchange discussion was:

> For every degree-at-most-two aligned shared-block mutation `B'` in the V6.1
> family, if all 52 champion witnesses are eliminated, then at least one newly
> introduced separator is rank-deficient (one of its two symbol maps is
> singular).

This is false. The exact mutation obtained by flipping position 5 has score 74,
retains 0 of the 52 old witnesses, and all 74 of its witnesses are in the
complete permutation pool. Thus it introduces no rank-deficient witness at all.
The machine-checkable details are in
`results/v7_lemma_falsification.json`; `scripts/audit_v7_lemma.py` recomputes
them from the saved exact incidence matrix and permutation pool.

The counterexample is small and structural: it is one aligned one-bit change,
not a sampled product candidate or a broad length-47 search. Other low-score
corners mix permutation and singular witnesses, so the data do not support a
replacement-family dichotomy after the lemma is weakened either.

## Status and limits

No proof or finite certificate for a surviving theorem was obtained. The exact
finite cover in `v6_1_exchange.structure.json` covers only the saved 480-row
dataset, and the 120-table pool covers only the permutation branch. The result
is therefore an exact computational falsification of this candidate lemma, not
a new theorem about shortest identities. The remaining mathematical gap is a
general structural statement relating the singular and permutation branches
for arbitrary shared blocks (or arbitrary length-47 pairs); this session does
not address it.
