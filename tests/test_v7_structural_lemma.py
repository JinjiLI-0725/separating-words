import json
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_v6_exchange import A, B, C, U, V, flip_many
from search_v4_4_witness_guided import endpoint_matrix, materialize_automata


def test_v7_counterexample_is_exact_and_permutation_only():
    result = json.loads(Path("results/v7_lemma_falsification.json").read_text())
    assert result["status"] == "falsified"
    assert result["old_score"] == 52
    assert result["mutation_score"] == 74
    assert result["old_retained"] == 0
    assert result["eliminated_old"] == 52
    assert result["introduced"] == 74
    assert result["permutation_pool_count"] == 74
    assert result["rank_deficient_replacements"] == 0
    assert result["counterexample"] is True

    # Recompute the two scores independently from transition tables.  This
    # keeps the regression tied to exact DFA evaluation rather than only to
    # the saved JSON certificate.
    mutation = (A + flip_many(B, [5]), flip_many(B, [5]) + C)
    exact = endpoint_matrix(materialize_automata(), [U, V, *mutation])
    assert int((exact[0] != exact[1]).sum()) == 52
    assert int((exact[2] != exact[3]).sum()) == 74

    pool = np.asarray(json.loads(Path("results/v6_permutation_pool.json").read_text())["transitions"], dtype=np.uint8)
    pool_endpoints = endpoint_matrix(pool, list(mutation))
    assert int((pool_endpoints[0] != pool_endpoints[1]).sum()) == 74
