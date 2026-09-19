"""Search for small DFAs separating two binary words."""

from dataclasses import dataclass

from separating_words.canonical_generator import generate_canonical_dfas
from separating_words.dfa import DFA


@dataclass(frozen=True)
class SeparationCertificate:
    states: int
    transitions: tuple[tuple[int, int], ...]
    x_final: int
    y_final: int


def find_separator(
    x: str,
    y: str,
    max_states: int = 5,
) -> SeparationCertificate | None:
    """Return a smallest DFA transition structure separating x and y."""

    if x == y:
        return None

    if any(c not in "01" for c in x + y):
        raise ValueError("words must be binary")

    for k in range(1, max_states + 1):
        for transitions in generate_canonical_dfas(k):
            dfa = DFA(transitions)

            x_final = dfa.run(x)
            y_final = dfa.run(y)

            if x_final != y_final:
                return SeparationCertificate(
                    states=k,
                    transitions=transitions,
                    x_final=x_final,
                    y_final=y_final,
                )

    return None


def separation_number(
    x: str,
    y: str,
    max_states: int = 5,
) -> int | None:
    certificate = find_separator(x, y, max_states)

    if certificate is None:
        return None

    return certificate.states
