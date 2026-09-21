# V2 rank-2 conceptual count

## Conclusion

The score-52 witness family has a short structural count. It is not necessary
to enumerate all 829 accessible rank-2 tables. There are only two possible
functional graphs for (f), separation forces the start to be the leaf of
their unique three-vertex tail, and elementary permutation incidences give

\[
52=12+40.
\]

The value 12 comes from the graph with two fixed points; 40 comes from the
graph with one 2-cycle. This explains the 52 witnesses for the fixed champion
pair. It is not a claim of global score optimality or a shortest-identity
theorem.

## Word algebra

Maps act on the right: in a product (rs), (s) acts first. Put

\[
p=T_1,\qquad f=T_0p,\qquad e=f^{12}.
\]

The common block has the word decomposition

```text
B = (10)^2 1 (10)^5 0 (10)^3 1.
```

Since (T_0=fp^{-1}), its map is

\[
b=pf^4p^{-1}f^5pf^2=ph,
\qquad h=f^4p^{-1}f^5pf^2.
\]

For

\[
U=(10)^{12}B,\qquad V=B(01)^{12},
\]

the two maps are

\[
U=phe,\qquad V=peh.
\]

Therefore, because (p) is a permutation,

\[
U(0)\ne V(0)\iff h(e(0))\ne e(h(0)). \tag{1}
\]

This endpoint identity uses the specific placement of the common block in
the champion pair. Rank\((e)=2\) alone does not imply it.

## What rank two forces

On the branch in question rank\((f)=4\) on five states. Thus exactly one
state has indegree zero, exactly one has indegree two, and all others have
indegree one in the functional graph of (f). Every transient depth and every
cycle length is at most four, and 12 is divisible by every possible cycle
length. Hence (f^{12}) maps every state onto the periodic set and fixes that
set pointwise. Since rank\((f^{12})=2\), there are exactly two periodic
states. There is only one indegree-zero state and only one excess incoming
edge, so the three transient states cannot branch: they form one chain

\[
x_3\longmapsto x_2\longmapsto x_1\longmapsto a.
\]

There are exactly two possibilities:

- (a,b) are fixed points;
- (a,b) form a 2-cycle.

In both cases (f^4=e). Since (h) begins with (f^4), its image lies in
(I=\operatorname{Im}(e)), so (eh=h). Equation (1) becomes

\[
U(0)\ne V(0)\iff h(e(0))\ne h(0). \tag{2}
\]

For rank two, both sides of (2) lie in the two-element set (I). This is
exactly the four-bucket classification: the two diagonal buckets do not
separate and the two off-diagonal buckets do. The purity of the buckets is
therefore symbolic, not empirical.

The facts that there are two image states and hence four buckets follow from
rank\((e)=2\). The formulas for (h), the identity (1), and the eventual
count in the off-diagonal buckets depend on the champion words.

## Why only the tail leaf can separate

Let (s) be the distinguished start. In the fixed-point case, (f^5=e), so

\[
h=Kf^2,\qquad K=ep^{-1}ep.
\]

In the 2-cycle case, (f^5=fe), so

\[
h=Kf^2,\qquad K=ep^{-1}fep.
\]

For (s=a,b,x_1,x_2), direct use of the tail gives

\[
f^2(s)=f^2(e(s)),
\]

and hence (h(s)=h(e(s))) for every permutation (p). Only (s=x_3)
survives: (f^2(x_3)=x_1), while (f^2(e(x_3))) is (a) in the fixed-point
case and (b) in the 2-cycle case.

Thus the start-at-leaf condition is necessary. It is not sufficient. The
saved certificate contains the lexicographically smallest accessible
separating and nonseparating canonical tables with the same fixed-point
functional graph and the same start role (x_3). This falsifies any formula
depending only on rank two, functional-graph type, and start role.

## The fixed-point contribution: 12

Here

\[
A=e^{-1}(a)=\{a,x_1,x_2,x_3\},\qquad e^{-1}(b)=\{b\}.
\]

For (y\in Q),

\[
K(y)=e\bigl(p^{-1}(e(p(y)))\bigr).
\]

The equality can fail between (y=x_1) and (y=a) only when (p(b)=a).
Under that condition, separation says that exactly one of (p(x_1)) and
(p(a)) is (b). Count the permutations:

- choose which of (x_1,a) maps to (b): 2 choices;
- choose the image of the other from (A\setminus\{a\}): 3 choices;
- biject the two remaining domain points with the two remaining images:
  (2!) choices.

Hence this functional graph contributes

\[
2\cdot3\cdot2=12. \tag{3}
\]

Every such pair is accessible: iterating (f) from (x_3) reaches
(x_2,x_1,a), and either (p(x_1)=b) or (p(a)=b) reaches the final state.

## The 2-cycle contribution: 40

Now

\[
A=e^{-1}(a)=\{a,x_2\},\qquad
B=e^{-1}(b)=\{b,x_1,x_3\}.
\]

Put \(\alpha=p^{-1}(a)\) and \(\beta=p^{-1}(b)\). From

\[
K(y)=e\bigl(p^{-1}(f(e(p(y))))\bigr)
\]

and the fact that (f) swaps (a,b), separation is equivalent to the two
simultaneous cross-incidences

\[
p(x_1),p(b)\text{ lie in different sets }A,B,
\quad
\alpha,\beta\text{ lie in different sets }A,B. \tag{4}
\]

Count (4) by the orientation of the representative preimages.

If \(\alpha\in A,\beta\in B\), choose \(\alpha\) in 2 ways. If \(\beta\) is
one of (x_1,b), the other distinguished point must occupy the remaining
(A)-slot; if \(\beta=x_3), either distinguished point may occupy it. The
remaining two images can be assigned in two ways. This gives 16.

If \(\alpha\in B,\beta\in A\), choose \(\beta\) in 2 ways. When \(\alpha)
is one of (x_1,b), the other distinguished point has two available
(B)-images and the last two images can be assigned in two ways; when
\(\alpha=x_3), either distinguished point occupies the remaining (A)-slot
and the other has two (B)-choices. This gives 24.

Therefore the 2-cycle graph contributes

\[
16+24=40. \tag{5}
\]

It is automatically accessible for every (p), since iterating (f) from
(x_3) already visits all five states.

## From labelled prototypes to canonical tables

Pointing state zero at one of (a,b,x_1,x_2,x_3) gives five pointed versions
of each functional graph, hence ten prototypes. Each pointed functional
graph has trivial relabelling stabilizer: the attached cycle state and every
tail position are intrinsically distinguished. Consequently each admissible
permutation (p) counted in (3) or (5) represents one distinct canonical
accessible transition table, and every table in the rank-4/
(T_1)-permutation, rank\((e)=2\) universe is represented once.

Combining (3) and (5) proves

\[
\boxed{52=12+40}.
\]

## Independent finite certificate

`scripts/analyze_v2_rank2_conceptual_count.py` constructs the ten pointed
prototypes directly and checks only their (10\cdot5!=1200) permutations.
It does not invoke the canonical DFA generator or read either previous
rank-2 result artifact. It independently recovers 829 accessible pairs,
verifies that only the two leaf prototypes separate, and checks the incidence
formulas above table by table. The result is saved in
`results/v2_rank2_conceptual_count.json`.

Reproduce with:

```sh
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v2_rank2_conceptual_count.py
PYTHONPATH=src:scripts .venv/bin/python -m pytest -q tests/test_v2_rank2_conceptual_count.py
```
