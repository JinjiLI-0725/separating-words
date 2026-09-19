"""Deterministic finite automata for the Separating Words project."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DFA:
    transitions: tuple[tuple[int, int], ...]
    start: int = 0

    @property
    def states(self) -> int:
        return len(self.transitions)

    def run(self, word: str) -> int:
        state = self.start

        for symbol in word:
            if symbol not in "01":
                raise ValueError("words must be binary")

            state = self.transitions[state][int(symbol)]

        return state

    def separates(self, x: str, y: str) -> bool:
        """
        A choice of accepting states separates x and y exactly when
        their final states differ.
        """
        return self.run(x) != self.run(y)
