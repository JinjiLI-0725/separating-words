"""Independent checks for the ten-prototype derivation of 52."""
import json
from pathlib import Path

from analyze_v2_rank2_conceptual_count import audit


def test_saved_conceptual_count_certificate():
    saved = json.loads(Path('results/v2_rank2_conceptual_count.json').read_text())
    assert saved['prototype_count'] == 10
    assert saved['total_small_checks'] == 1200
    assert saved['accessible_total'] == 829
    assert saved['separator_total'] == 52
    assert saved['conceptual_count']['two_fixed_points']['count'] == 12
    assert saved['conceptual_count']['two_cycle']['count'] == 40
    assert saved['conceptual_count']['total_expression'] == '12+40'


def test_ten_prototype_audit_recomputes_saved_counts():
    fresh = json.loads(json.dumps(audit()))
    saved = json.loads(Path('results/v2_rank2_conceptual_count.json').read_text())
    assert fresh == saved


def test_leaf_role_alone_has_exact_opposite_label_examples():
    saved = json.loads(Path('results/v2_rank2_conceptual_count.json').read_text())
    counterexample = saved['falsified_leaf_sufficiency']
    assert counterexample['same_kind'] == 'two_fixed_points'
    assert counterexample['same_start_role'] == 'x3'
    assert not counterexample['nonseparating']['separated']
    assert counterexample['separating']['separated']
