"""Independent regression checks for the finite rank-2 classification."""
import json
from pathlib import Path


def test_rank2_structural_certificate():
    result = json.loads(Path('results/v2_rank2_classification.json').read_text())
    assert result['rank2_universe_count'] == 829
    assert result['witness_count'] == 52
    assert result['coarse_bucket_count'] == 240
    assert result['coarse_conflicting_bucket_count'] == 34
    assert result['exact_bucket_count'] == 70
    assert result['exact_conflicting_bucket_count'] == 0
    assert result['witness_case_count'] == 11
    assert sum(case['count'] for case in result['witness_cases']) == 52
    assert result['witness_fibre_size_counts'] == {
        '(1, 4)': 1, '(2, 3)': 27, '(3, 2)': 13, '(4, 1)': 11}
