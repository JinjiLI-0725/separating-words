# V2 rank-2 structural classification

## Symbolic endpoint reduction

Write `p=T1`, `f=T0∘T1`, and let `b` be the map of the shared block

```text
B = 10101101010101001010101.
```

The fixed champion pair is

```text
U = (10)^12 B,       V = B (01)^12.
```

With composition acting right-to-left, define

```text
e = f^12,
h = f^4 p^-1 f^5 p f^2.
```

Cancellation inside `B` gives `b = p h`. Also the map of `(01)^12` is
`p e p^-1`. Therefore the endpoint maps are

```text
U = p h e,
V = p e h,
U(0) = p(h(e(0))),
V(0) = p(e(h(0))).
```

Since `p` is a bijection,

```text
U(0) != V(0)  iff  h(e(0)) != e(h(0)).
```

On the rank-4 branch every cycle and transient of `f` has length at most
4, so `e=f^12` is idempotent. The preceding equivalence is exact; it is
not a classifier inferred from aggregate statistics.

## Exact finite classification

There are 829 canonical accessible tables with rank(`e`)=2 in the complete
rank-4/T1-permutation universe. The 52 separators split into 11 cases.
For the ordered image states `a0<a1` of `e`, let `F_i=e^-1(a_i)` and let
`q(x)=i` when `x∈F_i`. Define the fibrewise `h` signature

```text
H = ((q(h(x)))_{x in F0}, (q(h(x)))_{x in F1}).
```

This does not assume that `h` induces a single-valued map on the quotient;
the entries can vary within one fibre. The pair `(zero_fibre,H)`, where
`zero_fibre` records which `F_i` contains state 0, is an exact classifier
over all 829 tables: its 70 buckets have no mixed separating/nonseparating
bucket. Eleven buckets are positive:

| zero fibre | H | count |
|---:|---|---:|
| 0 | ((0,1,1),(0,0)) | 3 |
| 0 | ((0,1,1),(1,1)) | 3 |
| 0 | ((0,1,1,1),(1,)) | 5 |
| 0 | ((1,0,0),(0,0)) | 4 |
| 0 | ((1,0,0),(1,1)) | 3 |
| 0 | ((1,0,0,0),(1,)) | 6 |
| 1 | ((0,),(1,0,0,0)) | 1 |
| 1 | ((0,0),(0,1,1)) | 3 |
| 1 | ((0,0),(1,0,0)) | 3 |
| 1 | ((1,1),(0,1,1)) | 10 |
| 1 | ((1,1),(1,0,0)) | 11 |

The counts sum directly to `3+3+5+4+3+6+1+3+3+10+11=52`.

The witnesses have fibre-size counts `(1,4):1`, `(2,3):27`,
`(3,2):13`, `(4,1):11`, and all six observed `T1` cycle types. The cycle
type is therefore descriptive but not a discriminator; it is retained in
the certificate as a within-case breakdown.

## Falsification of smaller candidates

The exact script exhaustively checks the 829 rank-2 tables. Rank(`e`)=2
alone leaves 777 nonseparators. The combined coarse signature consisting of
the ordered image states, fibre sizes, zero-fibre position, and `T1` cycle
type has 34 buckets containing both labels. The fibrewise `H` signature
alone has two such conflicts. Adding the pointed zero-fibre position removes
all conflicts. Thus the small classification requires pointed incidence
information; it is not a function of image/fibre sizes or `T1` cycle type.

This is an exact finite classification and count over the 829-table
rank-2 slice, not a closed-form count over all labelled maps. It avoids the
166,152-table enumeration and makes no claim that the 11 signatures are a
general theorem outside the stated finite universe.

## Combinatorial explanation of the count 52

Let `Im(e)={a0,a1}`, with `A=e^-1(a0)` and `B=e^-1(a1)`. Since `e` is an
idempotent projection, `e(a0)=a0` and `e(a1)=a1`. Put `r=e(0)`, so `r` is
the representative of the fibre containing 0. If `s=h(r)` and `t=e(h(0))`,
then `t` is `a0` or `a1` according to whether `h(0)` lies in `A` or `B`, and

```text
separation  iff  s != t.
```

This is the compact combinatorial form of the endpoint test. It is not,
however, a counting formula: knowing the fibre of `h(0)` and the fibrewise
image of `h` does not independently determine the compatible pairs `(f,p)`.
The equation `f^12=e` couples the functional graph of `f` to its transient
tails, while `h=f^4 p^-1 f^5 p f^2` couples those same data to the arbitrary
permutation `p`; accessibility and canonical first-discovery labels impose
additional coupled constraints.

The exhaustive certificate tests the strongest compact candidate found:
`(zero_fibre,H)`, where `H` is the fibrewise `h` signature above. It has 70
buckets and no mixed labels, with 11 positive buckets whose multiplicities
sum to 52. But this exactness is still a classification by the 829 finite
objects, not a derivation of those multiplicities from independent choices.
The ordered image states, fibre sizes, zero-fibre, and `T1` cycle type leave
34 mixed buckets; `H` without the zero-fibre leaves two mixed buckets. The
11 signatures also use all six observed `T1` cycle types, so cycle type does
not supply a further counting collapse.

Therefore no short non-enumerative combinatorial explanation of 52 was
found. The proved statement is the symbolic endpoint reduction. The exact
11-bucket count and the absence of mixed buckets are exhaustive finite
computational statements over the 829 rank-2 canonical tables, recorded by
`scripts/analyze_v2_rank2_classification.py`; they should not be promoted to
a closed-form counting lemma.

Reproduce with:

```sh
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v2_rank2_classification.py
PYTHONPATH=src:scripts .venv/bin/python -m pytest -q tests/test_v2_rank2_classification.py
```
