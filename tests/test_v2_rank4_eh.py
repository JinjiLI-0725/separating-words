"""Regression checks for the V2 rank-4 e/h reduction."""
import json
from pathlib import Path


def test_rank4_eh_summary_and_exact_certificate():
    result = json.loads(Path('results/v2_rank4_eh.json').read_text())
    assert result['universe_count'] == 4082
    assert result['separator_count'] == 52
    assert result['e_idempotent_for_all'] is True
    assert result['e_rank_counts'] == {'1': 461, '2': 829, '3': 1196, '4': 1596}
    assert result['champion_e_rank_counts'] == {'2': 52}
    assert sum(item['count'] for item in result['champion_incidence']) == 52
    for row in result['champion']:
        incidence = row['incidence']
        assert incidence['h_e0'] != incidence['e_h0']
        assert row['e_rank'] == 2

