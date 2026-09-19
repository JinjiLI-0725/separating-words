"""Enumerate reachable binary DFAs up to state relabeling.

Only transition structures matter for Separating Words:
a transition structure separates x and y iff the two words finish
in different states. Accepting states can then be chosen afterward.
"""

from itertools import product

from separating_words.dfa import DFA


def reachable_states(transitions):
    """Return states reachable from start state 0."""
    seen = {0}
    stack = [0]

    while stack:
        state = stack.pop()

        for nxt in transitions[state]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)

    return seen


def canonicalize(transitions):
    """Canonical relabeling by BFS from start state 0.

    Explore symbol 0 before symbol 1. For a reachable deterministic
    automaton this produces a unique numbering independent of the
    original labels.
    """
    mapping = {0: 0}
    order = [0]

    i = 0
    while i < len(order):
        state = order[i]

        for symbol in (0, 1):
            nxt = transitions[state][symbol]

            if nxt not in mapping:
                mapping[nxt] = len(mapping)
                order.append(nxt)

        i += 1

    canonical = []

    for old_state in order:
        canonical.append(
            tuple(mapping[transitions[old_state][symbol]]
                  for symbol in (0, 1))
        )

    return tuple(canonical)


def enumerate_canonical_dfas(k):
    """Enumerate reachable k-state binary transition structures.

    This simple reference implementation enumerates labeled transition
    tables and deduplicates their canonical forms. It is intended for
    validation at small k, not yet as the optimized k=5 engine.
    """
    canonical = set()

    # There are k^(2k) labeled transition tables.
    for flat in product(range(k), repeat=2 * k):
        transitions = tuple(
            (flat[2 * state], flat[2 * state + 1])
            for state in range(k)
        )

        if len(reachable_states(transitions)) != k:
            continue

        canonical.add(canonicalize(transitions))

    return tuple(sorted(canonical))


def as_dfas(k):
    return tuple(
        DFA(transitions)
        for transitions in enumerate_canonical_dfas(k)
    )
