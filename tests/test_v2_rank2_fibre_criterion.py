"""Regression checks for the rank-2 fibre criterion certificate."""
import json
from pathlib import Path


def test_rank2_fibre_criterion_certificate():
    result = json.loads(Path('results/v2_rank2_fibre_criterion.json').read_text())
    assert result['universe_count'] == 829
    assert result['separator_count'] == 52
    assert result['h_e0_in_image_count'] == 829
    assert result['criterion_bucket_counts'] == {
        '(0, 0)': {'count': 369, 'separating': 0},
        '(0, 1)': {'count': 24, 'separating': 24},
        '(1, 0)': {'count': 28, 'separating': 28},
        '(1, 1)': {'count': 408, 'separating': 0},
    }


def test_weaker_rank2_candidates_keep_explicit_counterexamples():
    result = json.loads(Path('results/v2_rank2_fibre_criterion.json').read_text())
    weaker = result['weaker_candidate_counterexamples']
    assert not weaker['rank_e_2_is_sufficient']['separated']
    pair = weaker['zero_fibre_and_h0_fibre_is_sufficient']
    assert pair['separating']['separated']
    assert not pair['nonseparating']['separated']
    assert pair['separating']['zero_fibre'] == pair['nonseparating']['zero_fibre']
    assert pair['separating']['h0_fibre'] == pair['nonseparating']['h0_fibre']
