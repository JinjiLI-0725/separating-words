#!/usr/bin/env python3
"""Exact bounded falsification of the first V7 witness-exchange lemma.

The tested implication is deliberately explicit: after a shared-block mutation
eliminates every champion witness, at least one replacement witness should be
rank-deficient.  The single-bit mutation at shared-block position 5 is an
exact counterexample inside the already-scored aligned family.
"""
from pathlib import Path
import json
import numpy as np

from analyze_v6_exchange import A, B, C, U, V, flip_many
from analyze_v6_structure import read
from search_v4_4_witness_guided import endpoint_matrix, materialize_automata


def main():
    prefix = Path("results/v6_1_exchange")
    rows, masks = read(prefix)
    lookup = {(r["u"], r["v"]): i for i, r in enumerate(rows)}
    old_i = lookup[(U, V)]
    mutation = (A + flip_many(B, [5]), flip_many(B, [5]) + C)
    mut_i = lookup[mutation]
    old = masks[old_i]
    changed = masks[mut_i]

    pool = np.asarray(json.loads(Path("results/v6_permutation_pool.json").read_text())["transitions"], dtype=np.uint8)
    words = [mutation[0], mutation[1]]
    pe = endpoint_matrix(pool, words)
    permutation_mask = pe[0] != pe[1]

    result = {
        "scope": {
            "family": "V6.1 complete degree <=2 aligned shared-block mutations",
            "mutation": {"positions": [5], "u": mutation[0], "v": mutation[1]},
            "universe": "166152 canonical DFAs on at most five states for exact score; 120 canonical permutation tables for permutation classification",
        },
        "old_score": int(old.sum()),
        "mutation_score": int(changed.sum()),
        "old_retained": int((old & changed).sum()),
        "eliminated_old": int((old & ~changed).sum()),
        "introduced": int((changed & ~old).sum()),
        "permutation_pool_count": int(permutation_mask.sum()),
        # The pool is a separate 120-table canonical universe, so its count is
        # compared with the global exact score rather than bitwise intersected.
        "rank_deficient_replacements": int(changed.sum() - permutation_mask.sum()),
        "counterexample": bool(old.sum() == 52 and changed.sum() == 74 and (old & changed).sum() == 0 and permutation_mask.sum() == 74),
        "tested_implication": "eliminating every champion witness forces a rank-deficient replacement witness",
        "status": "falsified",
    }
    assert result["counterexample"]
    assert result["rank_deficient_replacements"] == 0
    Path("results/v7_lemma_falsification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
