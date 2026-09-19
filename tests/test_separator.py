from separating_words.separator import (
    find_separator,
    separation_number,
)


def test_equal_words_have_no_separator():
    assert find_separator("0101", "0101") is None


def test_simple_pair_separated_by_two_states():
    assert separation_number("0", "1") == 2


def test_known_three_state_example():
    assert separation_number("1000", "0010") == 3


def test_certificate_really_separates():
    cert = find_separator("1000", "0010")

    assert cert is not None
    assert cert.states == 3
    assert cert.x_final != cert.y_final
