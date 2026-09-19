import pytest

from separating_words.dfa import DFA


def test_run():
    dfa = DFA((
        (1, 2),
        (1, 1),
        (2, 2),
    ))

    assert dfa.run("0") == 1
    assert dfa.run("1") == 2


def test_separates():
    dfa = DFA((
        (1, 2),
        (1, 1),
        (2, 2),
    ))

    assert dfa.separates("0010", "1000")


def test_equal_words_not_separated():
    dfa = DFA((
        (0, 1),
        (1, 0),
    ))

    assert not dfa.separates("0101", "0101")


def test_reject_nonbinary_input():
    dfa = DFA((
        (0, 1),
        (1, 0),
    ))

    with pytest.raises(ValueError):
        dfa.run("012")
