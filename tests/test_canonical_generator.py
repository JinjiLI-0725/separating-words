from separating_words.canonical_generator import generate_canonical_dfas
from separating_words.enumerate_dfa import enumerate_canonical_dfas


def test_direct_generator_no_duplicates():
    for k in (1, 2, 3):
        generated = list(generate_canonical_dfas(k))
        assert len(generated) == len(set(generated))


def test_direct_generator_matches_reference():
    for k in (1, 2, 3):
        direct = set(generate_canonical_dfas(k))
        reference = set(enumerate_canonical_dfas(k))

        assert direct == reference
