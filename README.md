# Separating Words — computational and structural study

A reproducible study of binary-word separation by deterministic finite automata and identities in finite transformation semigroups.

The repository now contains two complementary papers:

1. **Exact Computation of Near-Identities for Five-State Binary Automata** — the computational study that reproduces the known length-48 obstruction, identifies an explicit length-47 pair with score 52, and records bounded witness-exchange experiments.  
   Zenodo DOI: **10.5281/zenodo.22857868**

2. **Structural Classification of Five-State Separators for a Binary Near-Identity** — the structural follow-up explaining the 52 separators of the fixed length-47 pair. It derives the pointed endpoint criterion, localizes the witnesses to the rank-two slice, classifies the two possible functional-graph types, and obtains the conceptual count **52 = 12 + 40**.  
   Zenodo DOI: **10.5281/zenodo.22890295**  
   Manuscript: [papers/structural-classification/manuscript.pdf](papers/structural-classification/manuscript.pdf)  
   Source: [papers/structural-classification/manuscript.tex](papers/structural-classification/manuscript.tex)

The structural paper does **not** claim that score 52 is globally minimal among all distinct binary word pairs of length 47.

## Environment and quick verification

Run from the repository root on Linux. The audited environment uses CPython 3.10.12, NumPy 2.2.6 and pytest.

```sh
python3.10 -m venv .venv
.venv/bin/python -m pip install numpy==2.2.6 pytest==9.1.1
PYTHONPATH=src .venv/bin/python scripts/count_dfas.py
PYTHONPATH=src .venv/bin/python scripts/verify_bkss_48.py
PYTHONPATH=src:scripts .venv/bin/python -m pytest -q
```

Expected counts for exactly 1,...,5 states are `1, 12, 216, 5248, 160675` (total `166152`); the supplied length-48 pair has zero separators.

The k=5 ordered enumeration SHA-256 is:

```text
9982601f70cbf4f4deeed5f748db76352fa8700a52d6980a990a5a4b184b5d75
```

## Structural result

For the fixed length-47 pair

```text
U = (10)^12 B
V = B (01)^12
B = 10101101010101001010101
```

all 52 separators have five states, with one symbol acting as a permutation and the other as a rank-four map. Writing `p=T1`, `f=T0 p`, and `e=f^12`, separation reduces to the pointed endpoint condition

```text
h(e(0)) != e(h(0)).
```

All 52 witnesses lie in the rank-two slice of `e`. The functional graph of `f` then has a unique three-state tail and one of two periodic structures. Only the tail leaf can separate. The two cases contribute 12 and 40 witnesses, respectively:

```text
52 = 12 + 40
```

See [the structural manuscript](papers/structural-classification/manuscript.pdf) for the proof and scope.

## Meaning and limits

A score counts accessible binary transition tables, up to state relabeling fixing start state 0, whose two runs end at different states. Accepting sets are not counted.

The known shortest identity in the full transformation semigroup T5 has length 48. The present work studies the separator landscape immediately below that threshold. The explicit score-52 pair gives an upper bound for the corresponding length-47 extremal score, but this repository does not prove global optimality of 52.

## License and citation

The repository's original software/code is licensed under the [MIT License](LICENSE), copyright (c) 2026 Jinji Li. The papers and cited third-party literature retain their respective rights and licenses.

For the computational release, cite:

**Jinji Li. _Exact Computation of Near-Identities for Five-State Binary Automata_. Zenodo, 2026. DOI: 10.5281/zenodo.22857868.**

For the structural paper, cite:

**Jinji Li. _Structural Classification of Five-State Separators for a Binary Near-Identity_. Zenodo, 2026. DOI: 10.5281/zenodo.22890295.**
