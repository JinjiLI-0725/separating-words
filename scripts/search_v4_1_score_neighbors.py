#!/usr/bin/env python3

import json
import time
from pathlib import Path

from separating_words.canonical_generator import generate_canonical_dfas
from separating_words.dfa import DFA

RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

k = 5
L = 12

U = "01" * (k - 2 + L) + "10" * k + "01" * (k - 1)
V = "01" * (k - 2) + "10" * k + "01" * (k - 1 + L)

EXPECTED = 166_152


def delete_at(w, i):
    return w[:i] + w[i+1:]


def candidates():
    d = {}

    for i in range(48):
        u = delete_at(U, i)

        for j in range(48):
            v = delete_at(V, j)

            if u == v:
                continue

            d.setdefault((u, v), []).append((i, j))

    return d


def main():
    print("===== V4.1 ORDER-INDEPENDENT FITNESS =====", flush=True)

    pairs = candidates()
    keys = list(pairs)

    print(f"candidates={len(keys):,}", flush=True)

    # number of DFAs that DO separate each candidate
    separators = [0] * len(keys)

    total = 0
    start = time.time()

    for states in range(1, 6):

        for transitions in generate_canonical_dfas(states):

            dfa = DFA(transitions)
            total += 1

            for i, (u, v) in enumerate(keys):
                if dfa.run(u) != dfa.run(v):
                    separators[i] += 1

            if total % 10_000 == 0:
                print(
                    f"automata={total:,} "
                    f"elapsed={time.time()-start:.1f}s",
                    flush=True
                )

        print(
            f"completed k={states} total={total:,}",
            flush=True
        )

    assert total == EXPECTED

    ranking = []

    for i, (u, v) in enumerate(keys):
        sep = separators[i]
        indist = total - sep

        ranking.append({
            "u": u,
            "v": v,
            "length": 47,
            "separators": sep,
            "indistinguishable_dfas": indist,
            "indistinguishable_fraction": indist / total,
            "deletions": pairs[(u, v)],
        })

    ranking.sort(
        key=lambda x: (
            x["separators"],
            -len(x["deletions"])
        )
    )

    out = {
        "automata": total,
        "candidates": len(keys),
        "ranking": ranking,
    }

    Path("results/v4_1_scored_neighbors.json").write_text(
        json.dumps(out, indent=2)
    )

    print()
    print("===== TOP 20 =====")

    for rank, r in enumerate(ranking[:20], 1):
        print(
            f"{rank:2d}. "
            f"separators={r['separators']:,} "
            f"indist={r['indistinguishable_dfas']:,} "
            f"({100*r['indistinguishable_fraction']:.4f}%) "
            f"deletions={r['deletions'][:5]}"
        )
        print("    u =", r["u"])
        print("    v =", r["v"])

    if ranking[0]["separators"] == 0:
        print()
        print("EXACT LENGTH-47 HARD PAIR FOUND")


if __name__ == "__main__":
    main()
