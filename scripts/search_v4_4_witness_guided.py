#!/usr/bin/env python3

from __future__ import annotations

import itertools
import json
import time
from pathlib import Path

import numpy as np

from separating_words.canonical_generator import generate_canonical_dfas


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

WITNESS_FILE = RESULTS / "v4_3_witnesses.json"
OUTPUT = RESULTS / "v4_4_witness_guided.json"

EXPECTED_AUTOMATA = 166_152

SEED_U = "10101010101010101010101010101101010101001010101"
SEED_V = "10101101010101001010101010101010101010101010101"

assert len(SEED_U) == len(SEED_V) == 47


def flip_many(word, positions):
    chars = list(word)

    for i in positions:
        chars[i] = "1" if chars[i] == "0" else "0"

    return "".join(chars)


def run_word(transitions, word):
    q = 0

    for c in word:
        q = transitions[q][ord(c) - 48]

    return q


def load_witnesses():
    data = json.loads(WITNESS_FILE.read_text())

    assert data["witness_count"] == 52

    witnesses = []

    for row in data["witnesses"]:
        transitions = tuple(
            tuple(x) for x in row["transitions"]
        )
        witnesses.append(transitions)

    return witnesses


def witness_score(pair, witnesses):
    u, v = pair
    count = 0

    for transitions in witnesses:
        if run_word(transitions, u) != run_word(transitions, v):
            count += 1

    return count


def generate_candidates():
    """
    Structured escape neighborhood.

    A. Seed itself.

    B. Same two positions flipped in both words:
       C(47,2) = 1081.

    C. Two positions in u and corresponding positions shifted by 24
       in v whenever valid.

    D. Symmetric version: positions in v with +24 positions in u.

    E. Selected 3-bit coordinated flips using the same positions in
       both words.  C(47,3)=16215, still cheap against 52 witnesses.
    """

    candidates = {}

    def add(u, v, mutation):
        if u == v:
            return

        candidates.setdefault((u, v), []).append(mutation)

    add(SEED_U, SEED_V, {"type": "seed"})

    # Same-position 2-bit coordinated flips.
    for i, j in itertools.combinations(range(47), 2):
        add(
            flip_many(SEED_U, (i, j)),
            flip_many(SEED_V, (i, j)),
            {
                "type": "same_2",
                "u_positions": [i, j],
                "v_positions": [i, j],
            },
        )

    # Alignment suggested by V4.2: u position = v position + 24.
    aligned = [(i, i - 24) for i in range(24, 47)]

    for (ui1, vi1), (ui2, vi2) in itertools.combinations(aligned, 2):
        add(
            flip_many(SEED_U, (ui1, ui2)),
            flip_many(SEED_V, (vi1, vi2)),
            {
                "type": "offset24_2",
                "u_positions": [ui1, ui2],
                "v_positions": [vi1, vi2],
            },
        )

    # Three coordinated same-position flips.
    for pos in itertools.combinations(range(47), 3):
        add(
            flip_many(SEED_U, pos),
            flip_many(SEED_V, pos),
            {
                "type": "same_3",
                "u_positions": list(pos),
                "v_positions": list(pos),
            },
        )

    return candidates


def materialize_automata():
    rows = []

    for k in range(1, 6):
        for transitions in generate_canonical_dfas(k):
            padded = list(transitions)

            for q in range(k, 5):
                padded.append((q, q))

            rows.append(padded)

    T = np.asarray(rows, dtype=np.uint8)

    assert T.shape == (EXPECTED_AUTOMATA, 5, 2)

    return T


def encode(words):
    return np.asarray(
        [[ord(c) - 48 for c in w] for w in words],
        dtype=np.uint8,
    )


def endpoint_matrix(T, words, automata_batch=4096, word_batch=128):
    bits = encode(words)

    W, length = bits.shape
    A = T.shape[0]

    out = np.empty((W, A), dtype=np.uint8)

    for a0 in range(0, A, automata_batch):
        a1 = min(a0 + automata_batch, A)

        tb = T[a0:a1]
        B = a1 - a0
        ai = np.arange(B, dtype=np.intp)[:, None]

        for w0 in range(0, W, word_batch):
            w1 = min(w0 + word_batch, W)

            wb = bits[w0:w1]
            C = w1 - w0

            states = np.zeros((B, C), dtype=np.uint8)

            for p in range(length):
                states = tb[
                    ai,
                    states,
                    wb[:, p][None, :],
                ]

            out[w0:w1, a0:a1] = states.T

    return out


def full_scores(T, pairs):
    words = sorted({w for pair in pairs for w in pair})
    index = {w: i for i, w in enumerate(words)}

    print(
        f"full scoring {len(pairs):,} finalists "
        f"using {len(words):,} unique words",
        flush=True,
    )

    t0 = time.time()

    E = endpoint_matrix(T, words)

    print(
        f"full endpoint computation: "
        f"{time.time()-t0:.2f}s",
        flush=True,
    )

    scores = []

    for u, v in pairs:
        score = int(
            np.count_nonzero(
                E[index[u]] != E[index[v]]
            )
        )

        scores.append(score)

    return scores


def main():
    started = time.time()

    print("===== V4.4 WITNESS-GUIDED SEARCH =====")

    witnesses = load_witnesses()

    print(f"loaded witnesses = {len(witnesses)}")

    candidates = generate_candidates()

    print(f"structured candidates = {len(candidates):,}")

    # ---------------------------------------------------------
    # Stage 1: extremely cheap scoring against only 52 witnesses
    # ---------------------------------------------------------

    t0 = time.time()

    ranked = []

    for n, (pair, mutations) in enumerate(candidates.items(), 1):
        score = witness_score(pair, witnesses)

        ranked.append(
            {
                "pair": pair,
                "witness_score": score,
                "mutations": mutations,
            }
        )

        if n % 5000 == 0:
            print(
                f"witness filter {n:,}/{len(candidates):,}",
                flush=True,
            )

    ranked.sort(key=lambda x: x["witness_score"])

    witness_seconds = time.time() - t0

    print()
    print(
        f"witness filtering completed in "
        f"{witness_seconds:.2f}s"
    )

    print("best witness scores:")

    for row in ranked[:20]:
        print(
            row["witness_score"],
            row["mutations"][0],
        )

    zero_witness = sum(
        row["witness_score"] == 0
        for row in ranked
    )

    print(f"zero-on-old-witness candidates = {zero_witness:,}")

    # ---------------------------------------------------------
    # Stage 2: full exact scoring of only promising candidates
    # ---------------------------------------------------------

    # Always keep top 100. If there are candidates killing all
    # old witnesses, include up to first 500 of them.
    finalists = ranked[:100]

    zeros = [
        row for row in ranked
        if row["witness_score"] == 0
    ]

    seen = {row["pair"] for row in finalists}

    for row in zeros[:500]:
        if row["pair"] not in seen:
            finalists.append(row)
            seen.add(row["pair"])

    print()
    print(f"full-score finalists = {len(finalists):,}")

    T = materialize_automata()

    pairs = [row["pair"] for row in finalists]

    scores = full_scores(T, pairs)

    full_ranked = []

    for row, score in zip(finalists, scores):
        u, v = row["pair"]

        full_ranked.append(
            {
                "u": u,
                "v": v,
                "witness_score": row["witness_score"],
                "full_score": score,
                "indistinguishable": EXPECTED_AUTOMATA - score,
                "mutations": row["mutations"],
            }
        )

    full_ranked.sort(key=lambda x: x["full_score"])

    best = full_ranked[0]

    hard = [
        row for row in full_ranked
        if row["full_score"] == 0
    ]

    elapsed = time.time() - started

    payload = {
        "experiment": "V4.4 witness-guided structured search",
        "candidate_count": len(candidates),
        "old_witness_count": len(witnesses),
        "zero_old_witness_count": zero_witness,
        "finalist_count": len(finalists),
        "best_full_score": best["full_score"],
        "hard_pairs": len(hard),
        "elapsed_seconds": elapsed,
        "top": full_ranked[:100],
    }

    OUTPUT.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print()
    print("===== V4.4 RESULT =====")
    print(f"candidates = {len(candidates):,}")
    print(f"old witnesses = {len(witnesses):,}")
    print(f"zero against old witnesses = {zero_witness:,}")
    print(f"full-score finalists = {len(finalists):,}")
    print(f"best full score = {best['full_score']:,}")
    print(f"hard pairs = {len(hard):,}")
    print(f"elapsed = {elapsed:.2f}s")

    print()
    print("===== TOP 20 FULL SCORES =====")

    for i, row in enumerate(full_ranked[:20], 1):
        print(
            f"{i:2d}. full={row['full_score']:,} "
            f"old52={row['witness_score']}"
        )
        print(f"    mutations={row['mutations']}")
        print(f"    u={row['u']}")
        print(f"    v={row['v']}")

    if hard:
        print()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ZERO FULL-SCORE CANDIDATE FOUND")
        print("INDEPENDENT VERIFICATION REQUIRED")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        for row in hard:
            print("u =", row["u"])
            print("v =", row["v"])


if __name__ == "__main__":
    main()
