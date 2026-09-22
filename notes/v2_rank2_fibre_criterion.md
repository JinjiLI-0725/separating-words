# V2 rank-2 fibre criterion

Let (p=T_1), (f=T_0T_1), (e=f^{12}), and

\[
h=f^4p^{-1}f^5pf^2.
\]

The fixed champion pair already has the exact endpoint reduction

\[
U(0)\ne V(0)\quad\Longleftrightarrow\quad h(e(0))\ne e(h(0)).
\]

On the rank-4 branch every transient of (f) has length at most four.
Thus (f^4) sends every state to an (f)-cycle, while
\(\operatorname{Im}(e)=\operatorname{Im}(f^{12})\) is precisely the set of
(f)-cycle states. Since (h) begins with (f^4),

\[
h(e(0))\in\operatorname{Im}(e).
\]

Now suppose \(\operatorname{rank}(e)=2\). Write
\(\operatorname{Im}(e)=\{a_0,a_1\}\), with (F_i=e^{-1}(a_i)), and define
\(\iota(x)=i\) when (x\in F_i). Because (e(h(0))=a_{\iota(h(0))}),
the endpoint condition becomes the purely pointed fibre test

\[
\boxed{\quad U(0)\ne V(0)
 \quad\Longleftrightarrow\quad
 \iota(h(0))\ne \operatorname{index}(h(e(0)))\quad}.
\]

The right side compares the fibre containing (h(0)) with the image
representative reached from the distinguished representative (e(0)). It
does not require the zero-fibre position, the full fibrewise action of (h),
or a (T_1) cycle type.

## Exact finite audit

The script `scripts/analyze_v2_rank2_fibre_criterion.py` checks the complete
829-table rank-2 slice. In every table (h(e(0))\in\operatorname{Im}(e)),
and the four possible pairs of indices are pure:

| fibre index of (h(0)) | image index of (h(e(0))) | tables | separators |
|---:|---:|---:|---:|
| 0 | 0 | 369 | 0 |
| 0 | 1 | 24 | 24 |
| 1 | 0 | 28 | 28 |
| 1 | 1 | 408 | 0 |

This replaces the previous 70-bucket exact signature and its 11 positive
signatures with a two-index necessary-and-sufficient criterion. The theorem
above is algebraic; the assertion that this slice contains exactly 829
canonical tables and 52 separators, and the bucket counts, are exhaustive
computational classifications over that finite universe.

The artifact also records smallest canonical counterexamples to two weaker
proposals: rank\((e)=2\) alone, and the pair consisting of the zero-fibre
position and the fibre containing (h(0)). Reproduce with:

```sh
PYTHONPATH=src:scripts .venv/bin/python scripts/analyze_v2_rank2_fibre_criterion.py
PYTHONPATH=src:scripts .venv/bin/python -m pytest -q tests/test_v2_rank2_fibre_criterion.py
```
