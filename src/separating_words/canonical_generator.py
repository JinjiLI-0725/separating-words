"""Direct generation of canonical accessible binary DFA transition structures.

States are numbered by first discovery from state 0, scanning transitions
in the fixed order

    (state 0, symbol 0),
    (state 0, symbol 1),
    (state 1, symbol 0),
    (state 1, symbol 1),
    ...

Therefore a transition may point to:
    - any already discovered state, or
    - exactly the next undiscovered state.

This is a restricted-growth representation and removes state-label
symmetry during generation.
"""

from collections.abc import Iterator

Transitions = tuple[tuple[int, int], ...]


def generate_canonical_dfas(k: int) -> Iterator[Transitions]:
    """Yield every accessible canonical k-state binary transition table."""

    if k < 1:
        raise ValueError("k must be at least 1")

    flat = [0] * (2 * k)

    def backtrack(pos: int, discovered: int):
        if pos == 2 * k:
            if discovered == k:
                yield tuple(
                    (flat[2 * state], flat[2 * state + 1])
                    for state in range(k)
                )
            return

        source = pos // 2

        # We cannot define transitions out of a state that has not yet
        # been discovered.
        if source >= discovered:
            return

        # Existing states are 0,...,discovered-1.
        # We may additionally introduce exactly state `discovered`.
        upper = discovered if discovered < k else discovered - 1

        for target in range(upper + 1):
            flat[pos] = target

            if target == discovered:
                yield from backtrack(pos + 1, discovered + 1)
            else:
                yield from backtrack(pos + 1, discovered)

    yield from backtrack(0, 1)
