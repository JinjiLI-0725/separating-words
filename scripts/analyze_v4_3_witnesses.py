#!/usr/bin/env python3

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from separating_words.canonical_generator import generate_canonical_dfas
from separating_words.dfa import DFA


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

OUTPUT = RESULTS / "v4_3_witnesses.json"

U = "10101010101010101010101010101101010101001010101"
V = "10101101010101001010101010101010101010101010101"

assert len(U) == len(V) == 47


def trace(transitions, word):
    q = 0
    states = [q]

    for c in word:
        q = transitions[q][int(c)]
        states.append(q)

    return states


def main():
    witnesses = []
    total = 0
    by_k = Counter()
    endpoint_pairs = Counter()

    print("===== V4.3 WITNESS ANALYSIS =====")

    for k in range(1, 6):
        local_total = 0
        local_sep = 0

        for index, transitions in enumerate(
            generate_canonical_dfas(k)
        ):
            total += 1
            local_total += 1

            dfa = DFA(transitions)

            fu = dfa.run(U)
            fv = dfa.run(V)

            if fu == fv:
                continue

            local_sep += 1
            by_k[k] += 1
            endpoint_pairs[(k, fu, fv)] += 1

            tu = trace(transitions, U)
            tv = trace(transitions, V)

            # Positions after which the two runs occupy
            # different states.
            divergence_positions = [
                i
                for i, (a, b) in enumerate(zip(tu, tv))
                if a != b
            ]

            witnesses.append(
                {
                    "k": k,
                    "index_within_k": index,
                    "transitions": transitions,
                    "final_u": fu,
                    "final_v": fv,
                    "trace_u": tu,
                    "trace_v": tv,
                    "divergence_positions": divergence_positions,
                }
            )

        print(
            f"k={k}: automata={local_total:,} "
            f"separators={local_sep:,}"
        )

    print()
    print(f"total automata = {total:,}")
    print(f"total witnesses = {len(witnesses):,}")

    if len(witnesses) != 52:
        raise RuntimeError(
            f"expected exactly 52 witnesses, got {len(witnesses)}"
        )

    print()
    print("===== WITNESSES BY STATE COUNT =====")

    for k in range(1, 6):
        print(f"k={k}: {by_k[k]}")

    print()
    print("===== FINAL ENDPOINT PATTERNS =====")

    for key, count in endpoint_pairs.most_common():
        k, fu, fv = key
        print(
            f"k={k} final=({fu},{fv}) count={count}"
        )

    # Aggregate where witness traces differ.
    position_counts = Counter()

    for w in witnesses:
        for p in w["divergence_positions"]:
            position_counts[p] += 1

    print()
    print("===== TRACE DIVERGENCE BY POSITION =====")
    print("position = state after reading that many symbols")
    print()

    for p in range(48):
        count = position_counts[p]

        if count:
            marker = ""

            if count == len(witnesses):
                marker = "  <-- ALL 52"

            print(
                f"{p:2d}: {count:2d}/{len(witnesses)}{marker}"
            )

    payload = {
        "u": U,
        "v": V,
        "length": 47,
        "automata_checked": total,
        "witness_count": len(witnesses),
        "by_state_count": dict(by_k),
        "endpoint_patterns": [
            {
                "k": k,
                "final_u": fu,
                "final_v": fv,
                "count": count,
            }
            for (k, fu, fv), count
            in endpoint_pairs.most_common()
        ],
        "trace_divergence_counts": {
            str(p): position_counts[p]
            for p in range(48)
        },
        "witnesses": witnesses,
    }

    OUTPUT.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"saved -> {OUTPUT}")


if __name__ == "__main__":
    main()
