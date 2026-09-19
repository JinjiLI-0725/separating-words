#!/usr/bin/env python3

"""
V4.1-fast

Order-independent scoring of all unique length-47 one-symbol-deletion
neighbors of the verified BKSS length-48 pair.

For every candidate pair (u,v), count exactly how many canonical
<=5-state DFAs separate it.

Fitness:
    separators(u,v)

A genuine hard pair has separators == 0.

This version vectorizes over all candidate words for each DFA.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from separating_words.canonical_generator import generate_canonical_dfas


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

OUTPUT = RESULTS / "v4_1_fast_scored_neighbors.json"
CHECKPOINT = RESULTS / "v4_1_fast_checkpoint.json"

EXPECTED_AUTOMATA = 166_152

k = 5
L = 12

U = "01" * (k - 2 + L) + "10" * k + "01" * (k - 1)
V = "01" * (k - 2) + "10" * k + "01" * (k - 1 + L)

assert len(U) == 48
assert len(V) == 48


def delete_at(word: str, i: int) -> str:
    return word[:i] + word[i + 1:]


def generate_candidates():
    by_pair = {}

    for i in range(48):
        u = delete_at(U, i)

        for j in range(48):
            v = delete_at(V, j)

            if u == v:
                continue

            by_pair.setdefault((u, v), []).append((i, j))

    keys = list(by_pair)

    return keys, by_pair


def encode_words(words):
    """
    Shape:
        (#words, 47)

    Values:
        uint8 0/1
    """
    return np.asarray(
        [[ord(c) - 48 for c in word] for word in words],
        dtype=np.uint8,
    )


def final_states_vectorized(symbols, transitions):
    """
    Run one DFA on ALL words simultaneously.

    symbols:
        shape (num_words, word_length)

    transitions:
        tuple of (zero_target, one_target)

    returns:
        final state for each word
    """

    num_words = symbols.shape[0]

    states = np.zeros(num_words, dtype=np.uint8)

    table = np.asarray(transitions, dtype=np.uint8)

    for column in range(symbols.shape[1]):
        states = table[states, symbols[:, column]]

    return states


def main():
    print("===== V4.1 FAST =====", flush=True)

    keys, deletion_map = generate_candidates()

    print(
        f"unique candidates = {len(keys):,}",
        flush=True,
    )

    u_words = [u for u, _ in keys]
    v_words = [v for _, v in keys]

    U_symbols = encode_words(u_words)
    V_symbols = encode_words(v_words)

    assert U_symbols.shape == (len(keys), 47)
    assert V_symbols.shape == (len(keys), 47)

    # Exact count of DFAs separating each candidate.
    separators = np.zeros(len(keys), dtype=np.uint32)

    total = 0
    started = time.time()

    for states_count in range(1, 6):

        local = 0

        for transitions in generate_canonical_dfas(states_count):
            uf = final_states_vectorized(U_symbols, transitions)
            vf = final_states_vectorized(V_symbols, transitions)

            separators += (uf != vf)

            total += 1
            local += 1

            if total % 10_000 == 0:
                elapsed = time.time() - started

                best = int(separators.min())

                print(
                    f"automata={total:,} "
                    f"best_separators_so_far={best:,} "
                    f"elapsed={elapsed:.1f}s",
                    flush=True,
                )

        print(
            f"completed k={states_count}: "
            f"local={local:,} "
            f"cumulative={total:,}",
            flush=True,
        )

    elapsed = time.time() - started

    if total != EXPECTED_AUTOMATA:
        raise RuntimeError(
            f"expected {EXPECTED_AUTOMATA:,} automata, "
            f"got {total:,}"
        )

    ranking = []

    for idx, (u, v) in enumerate(keys):

        sep = int(separators[idx])
        indist = total - sep

        ranking.append(
            {
                "u": u,
                "v": v,
                "length": 47,
                "separators": sep,
                "indistinguishable_dfas": indist,
                "indistinguishable_fraction": indist / total,
                "deletion_examples": deletion_map[(u, v)],
                "deletion_multiplicity": len(
                    deletion_map[(u, v)]
                ),
            }
        )

    ranking.sort(
        key=lambda row: (
            row["separators"],
            -row["deletion_multiplicity"],
        )
    )

    hard_pairs = [
        row for row in ranking
        if row["separators"] == 0
    ]

    output = {
        "experiment": "V4.1 fast BKSS deletion scoring",
        "automata": total,
        "candidates": len(keys),
        "elapsed_seconds": elapsed,
        "hard_pairs": len(hard_pairs),
        "ranking": ranking,
    }

    OUTPUT.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    CHECKPOINT.write_text(
        json.dumps(
            {
                "phase": "v4_1_fast",
                "automata": total,
                "candidates": len(keys),
                "best_separators": ranking[0]["separators"],
                "hard_pairs": len(hard_pairs),
                "elapsed_seconds": elapsed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("===== FINAL RESULT =====")
    print(f"automata = {total:,}")
    print(f"candidates = {len(keys):,}")
    print(f"time = {elapsed:.2f}s")
    print(f"hard pairs = {len(hard_pairs):,}")
    print()

    print("===== TOP 20 =====")

    for rank, row in enumerate(ranking[:20], 1):

        print(
            f"{rank:2d}. "
            f"separators={row['separators']:,} "
            f"indist={row['indistinguishable_dfas']:,} "
            f"({100 * row['indistinguishable_fraction']:.4f}%) "
            f"deletions={row['deletion_examples'][:5]}"
        )

        print(f"    u={row['u']}")
        print(f"    v={row['v']}")

    if hard_pairs:

        print()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("EXACT LENGTH-47 HARD PAIR FOUND")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        for row in hard_pairs:
            print()
            print("u =", row["u"])
            print("v =", row["v"])

    else:

        print()
        print(
            "No exact hard pair in the one-deletion "
            "BKSS neighborhood."
        )


if __name__ == "__main__":
    main()
