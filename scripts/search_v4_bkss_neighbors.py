#!/usr/bin/env python3

"""
V4: targeted search around the verified BKSS length-48 hard pair.

Phase 1:
    Delete one symbol from u and one symbol from v.
    Deduplicate the resulting equal-length 47-bit pairs.

Phase 2:
    Stream through every canonical DFA with <=5 states.
    For each candidate, record the first DFA that separates it.
    Candidates die permanently once separated.

The interesting quantity is survival depth:
    how many canonical DFAs a candidate survives before the first separator.

If any candidate survives all 166,152 DFAs, we have an exact
length-47 hard pair.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from separating_words.canonical_generator import generate_canonical_dfas


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

RECORDS = RESULTS / "v4_bkss_neighbors.json"
CHECKPOINT = RESULTS / "v4_bkss_neighbors_checkpoint.json"

EXPECTED_AUTOMATA = 166_152


# ----------------------------------------------------------------------
# BKSS pair
# ----------------------------------------------------------------------

k = 5
L = 12

BKSS_U = "01" * (k - 2 + L) + "10" * k + "01" * (k - 1)
BKSS_V = "01" * (k - 2) + "10" * k + "01" * (k - 1 + L)

assert len(BKSS_U) == 48
assert len(BKSS_V) == 48
assert BKSS_U != BKSS_V


@dataclass
class Candidate:
    u: str
    v: str
    deletion_examples: list[tuple[int, int]]
    survived: int = 0
    separator_states: int | None = None
    separator_index: int | None = None
    separator_transitions: tuple[tuple[int, int], ...] | None = None


# ----------------------------------------------------------------------
# Candidate generation
# ----------------------------------------------------------------------

def delete_at(word: str, i: int) -> str:
    return word[:i] + word[i + 1:]


def generate_candidates() -> list[Candidate]:
    """
    All unique ordered pairs obtained by deleting one position from
    BKSS_U and one position from BKSS_V.
    """
    by_pair: dict[tuple[str, str], list[tuple[int, int]]] = {}

    for i in range(len(BKSS_U)):
        u = delete_at(BKSS_U, i)

        for j in range(len(BKSS_V)):
            v = delete_at(BKSS_V, j)

            if u == v:
                # Equal words are irrelevant.
                continue

            key = (u, v)
            by_pair.setdefault(key, []).append((i, j))

    candidates = [
        Candidate(
            u=u,
            v=v,
            deletion_examples=examples,
        )
        for (u, v), examples in by_pair.items()
    ]

    return candidates


# ----------------------------------------------------------------------
# Fast DFA evaluation
# ----------------------------------------------------------------------

def run_word(word: str, transitions: tuple[tuple[int, int], ...]) -> int:
    state = 0
    for c in word:
        state = transitions[state][ord(c) - 48]
    return state


def evaluate_candidates(candidates: list[Candidate]) -> tuple[int, list[int]]:
    """
    Stream DFAs once.

    A candidate remains active until the first DFA sends its two words
    to different final states.

    Returns:
        total number of automata checked
        indices of candidates surviving every automaton
    """

    active = np.ones(len(candidates), dtype=bool)
    total = 0
    started = time.time()

    print(f"initial active candidates = {active.sum():,}")

    for states in range(1, 6):
        state_count = 0

        for transitions in generate_canonical_dfas(states):
            total += 1
            state_count += 1

            active_indices = np.flatnonzero(active)

            if len(active_indices) == 0:
                print("all candidates separated; stopping early")
                return total, []

            for idx in active_indices:
                candidate = candidates[int(idx)]

                uf = run_word(candidate.u, transitions)
                vf = run_word(candidate.v, transitions)

                if uf != vf:
                    candidate.survived = total - 1
                    candidate.separator_states = states
                    candidate.separator_index = total
                    candidate.separator_transitions = transitions
                    active[idx] = False

            if total % 10_000 == 0:
                elapsed = time.time() - started
                print(
                    f"automata={total:,} "
                    f"active={active.sum():,} "
                    f"elapsed={elapsed:.1f}s"
                )

        print(
            f"completed k={states}: "
            f"automata={state_count:,} "
            f"active={active.sum():,}"
        )

    survivors = [int(i) for i in np.flatnonzero(active)]

    for idx in survivors:
        candidates[idx].survived = total

    return total, survivors


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

def candidate_to_dict(c: Candidate) -> dict:
    return {
        "u": c.u,
        "v": c.v,
        "length": len(c.u),
        "deletion_examples": c.deletion_examples[:20],
        "deletion_multiplicity": len(c.deletion_examples),
        "survived_automata": c.survived,
        "separator_states": c.separator_states,
        "separator_index": c.separator_index,
        "separator_transitions": c.separator_transitions,
    }


def main() -> None:
    print("===== SEPARATING WORDS V4 =====")
    print("BKSS targeted length-47 neighborhood search")
    print()
    print("BKSS u =", BKSS_U)
    print("BKSS v =", BKSS_V)
    print()

    candidates = generate_candidates()

    print(f"raw deletion pairs = {48 * 48:,}")
    print(f"unique nontrivial candidates = {len(candidates):,}")
    print()

    started = time.time()

    total, survivors = evaluate_candidates(candidates)

    elapsed = time.time() - started

    ranked = sorted(
        candidates,
        key=lambda c: (
            c.survived,
            len(c.deletion_examples),
        ),
        reverse=True,
    )

    output = {
        "experiment": "BKSS one-symbol deletion neighborhood",
        "source_length": 48,
        "target_length": 47,
        "canonical_automata_checked": total,
        "expected_automata": EXPECTED_AUTOMATA,
        "unique_candidates": len(candidates),
        "exact_survivors": len(survivors),
        "elapsed_seconds": elapsed,
        "top_candidates": [
            candidate_to_dict(c)
            for c in ranked[:50]
        ],
        "exact_hard_pairs": [
            candidate_to_dict(candidates[i])
            for i in survivors
        ],
    }

    RECORDS.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    CHECKPOINT.write_text(
        json.dumps(
            {
                "phase": "v4_bkss_neighbors",
                "target_length": 47,
                "automata_checked": total,
                "candidates": len(candidates),
                "exact_survivors": len(survivors),
                "elapsed_seconds": elapsed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("===== V4 RESULT =====")
    print(f"automata checked = {total:,}")
    print(f"candidates = {len(candidates):,}")
    print(f"exact survivors = {len(survivors):,}")
    print(f"time = {elapsed:.2f}s")
    print()

    print("Top 10 candidates by survival depth:")

    for rank, candidate in enumerate(ranked[:10], 1):
        print(
            f"{rank:2d}. survived={candidate.survived:,} "
            f"sep_k={candidate.separator_states} "
            f"sep_index={candidate.separator_index} "
            f"multiplicity={len(candidate.deletion_examples)}"
        )
        print(f"    u={candidate.u}")
        print(f"    v={candidate.v}")
        print(
            f"    deletion examples="
            f"{candidate.deletion_examples[:5]}"
        )

    print()

    if survivors:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("EXACT LENGTH-47 HARD PAIR(S) FOUND")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        for idx in survivors:
            c = candidates[idx]
            print()
            print("u =", c.u)
            print("v =", c.v)

    else:
        print(
            "No exact length-47 hard pair exists "
            "inside this one-deletion BKSS neighborhood."
        )
        print(
            "This is NOT a proof that no length-47 hard pair exists."
        )


if __name__ == "__main__":
    main()
