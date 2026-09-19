from separating_words.enumerate_dfa import (
    canonicalize,
    enumerate_canonical_dfas,
    reachable_states,
)


def test_reachable_states():
    transitions = (
        (1, 0),
        (1, 2),
        (2, 2),
    )

    assert reachable_states(transitions) == {0, 1, 2}


def test_unreachable_state():
    transitions = (
        (0, 0),
        (1, 1),
    )

    assert reachable_states(transitions) == {0}


def test_canonicalization_removes_state_names():
    a = (
        (1, 2),
        (1, 0),
        (2, 1),
    )

    # Swap original labels 1 and 2 while keeping start state 0.
    b = (
        (2, 1),
        (1, 2),
        (2, 0),
    )

    assert canonicalize(a) == canonicalize(b)


def test_small_counts():
    counts = {
        k: len(enumerate_canonical_dfas(k))
        for k in (1, 2, 3)
    }

    print("canonical DFA counts:", counts)

    assert counts[1] == 1
    assert counts[2] > counts[1]
    assert counts[3] > counts[2]

def test_canonicalization_invariant_under_all_relabelings():
    from itertools import permutations

    examples = (
        (
            (1, 2),
            (1, 0),
            (2, 1),
        ),
        (
            (1, 2),
            (2, 0),
            (0, 1),
        ),
    )

    for transitions in examples:
        expected = canonicalize(transitions)
        k = len(transitions)

        for tail in permutations(range(1, k)):
            permutation = (0,) + tail

            # old state -> new label
            relabeled = [None] * k

            for old in range(k):
                new = permutation[old]

                relabeled[new] = tuple(
                    permutation[transitions[old][symbol]]
                    for symbol in (0, 1)
                )

            assert canonicalize(tuple(relabeled)) == expected
