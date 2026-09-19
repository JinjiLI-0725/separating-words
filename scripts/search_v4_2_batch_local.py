#!/usr/bin/env python3

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from separating_words.canonical_generator import generate_canonical_dfas


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

OUTPUT = RESULTS / "v4_2_batch_local.json"

EXPECTED_AUTOMATA = 166_152

# Verified BKSS length-48 pair
BKSS_U = "01" * 15 + "10" * 5 + "01" * 4
BKSS_V = "01" * 3 + "10" * 5 + "01" * 16

# V4.1 champion: deletion (0,0), exact score = 52
SEED_U = "10101010101010101010101010101101010101001010101"
SEED_V = "10101101010101001010101010101010101010101010101"

assert len(BKSS_U) == len(BKSS_V) == 48
assert len(SEED_U) == len(SEED_V) == 47


def flip(word: str, i: int) -> str:
    c = "1" if word[i] == "0" else "0"
    return word[:i] + c + word[i + 1:]


def load_automata():
    """
    Materialize every canonical <=5-state transition structure.

    Shape:
        (166152, 5, 2)

    Smaller automata are padded with self-loops on otherwise unreachable
    states. Starting from state 0, padding cannot affect their behavior.
    """
    rows = []

    counts = {}

    for k in range(1, 6):
        count = 0

        for transitions in generate_canonical_dfas(k):
            padded = list(transitions)

            for q in range(k, 5):
                padded.append((q, q))

            rows.append(padded)
            count += 1

        counts[k] = count
        print(f"loaded k={k}: {count:,}", flush=True)

    T = np.asarray(rows, dtype=np.uint8)

    assert T.shape == (EXPECTED_AUTOMATA, 5, 2), T.shape

    print(f"automata array shape = {T.shape}", flush=True)
    print(f"automata memory = {T.nbytes / 1024**2:.2f} MB", flush=True)

    return T, counts


def encode(words):
    lengths = {len(w) for w in words}

    if len(lengths) != 1:
        raise ValueError("all words in a batch must have equal length")

    return np.asarray(
        [[ord(c) - 48 for c in w] for w in words],
        dtype=np.uint8,
    )


def endpoints(T, words, automata_batch=4096, word_batch=128):
    """
    Compute final states for every (word, automaton).

    Return shape:
        (#words, #automata)

    We batch both dimensions to keep temporary arrays bounded.
    """
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
                symbols = wb[:, p][None, :]
                states = tb[ai, states, symbols]

            out[w0:w1, a0:a1] = states.T

    return out


def score_pairs(T, pairs, automata_batch=4096, word_batch=128):
    """
    Exact separator counts for candidate pairs.

    Deduplicate words first so shared words are evaluated once.
    """
    words = sorted({w for pair in pairs for w in pair})
    word_index = {w: i for i, w in enumerate(words)}

    print(
        f"scoring {len(pairs):,} pairs "
        f"using {len(words):,} unique words",
        flush=True,
    )

    t0 = time.time()

    E = endpoints(
        T,
        words,
        automata_batch=automata_batch,
        word_batch=word_batch,
    )

    print(
        f"endpoint matrix = {E.shape}, "
        f"{E.nbytes / 1024**2:.1f} MB, "
        f"time={time.time()-t0:.2f}s",
        flush=True,
    )

    scores = np.empty(len(pairs), dtype=np.uint32)

    # Candidate comparison itself is cheap once endpoints are cached.
    for i, (u, v) in enumerate(pairs):
        scores[i] = np.count_nonzero(
            E[word_index[u]] != E[word_index[v]]
        )

    return scores


def regression_checks(T):
    print()
    print("===== REGRESSION CHECKS =====", flush=True)

    # Check 1: known BKSS hard pair must score zero.
    scores = score_pairs(T, [(BKSS_U, BKSS_V)])

    bkss_score = int(scores[0])

    print(f"BKSS length-48 score = {bkss_score}", flush=True)

    if bkss_score != 0:
        raise RuntimeError(
            f"BKSS regression failed: expected 0, got {bkss_score}"
        )

    # Check 2: V4.1 champion must reproduce exact score 52.
    scores = score_pairs(T, [(SEED_U, SEED_V)])

    seed_score = int(scores[0])

    print(f"V4.1 seed score = {seed_score}", flush=True)

    if seed_score != 52:
        raise RuntimeError(
            f"seed regression failed: expected 52, got {seed_score}"
        )

    print("REGRESSION CHECKS PASSED", flush=True)


def generate_neighborhood():
    """
    Complete local neighborhood:

      original seed                     1
      flip one bit in u                47
      flip one bit in v                47
      flip one bit in both          47*47

    Total before deduplication = 2304.
    """

    by_pair = {}

    def add(u, v, mutation):
        if u == v:
            return

        by_pair.setdefault((u, v), []).append(mutation)

    add(SEED_U, SEED_V, {"type": "seed"})

    for i in range(47):
        add(
            flip(SEED_U, i),
            SEED_V,
            {"type": "flip_u", "i": i},
        )

    for j in range(47):
        add(
            SEED_U,
            flip(SEED_V, j),
            {"type": "flip_v", "j": j},
        )

    for i in range(47):
        fu = flip(SEED_U, i)

        for j in range(47):
            add(
                fu,
                flip(SEED_V, j),
                {"type": "flip_both", "i": i, "j": j},
            )

    return list(by_pair), by_pair


def main():
    started = time.time()

    print("===== V4.2 BATCH LOCAL SEARCH =====", flush=True)

    T, counts = load_automata()

    print("counts =", counts, flush=True)

    regression_checks(T)

    pairs, mutation_map = generate_neighborhood()

    print()
    print("===== LOCAL SEARCH =====", flush=True)
    print(f"candidate pairs = {len(pairs):,}", flush=True)

    t0 = time.time()

    scores = score_pairs(T, pairs)

    search_seconds = time.time() - t0

    ranking = []

    for idx, (u, v) in enumerate(pairs):
        score = int(scores[idx])

        ranking.append(
            {
                "u": u,
                "v": v,
                "separators": score,
                "indistinguishable": EXPECTED_AUTOMATA - score,
                "mutations": mutation_map[(u, v)],
            }
        )

    ranking.sort(key=lambda x: x["separators"])

    best = ranking[0]

    hard = [r for r in ranking if r["separators"] == 0]

    total_seconds = time.time() - started

    result = {
        "experiment": "V4.2 batch local search",
        "automata": EXPECTED_AUTOMATA,
        "candidate_pairs": len(pairs),
        "seed_score": 52,
        "best_score": best["separators"],
        "hard_pairs": len(hard),
        "search_seconds": search_seconds,
        "total_seconds": total_seconds,
        "ranking": ranking,
    }

    OUTPUT.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print()
    print("===== V4.2 RESULT =====")
    print(f"candidate pairs = {len(pairs):,}")
    print(f"seed score = 52")
    print(f"best score = {best['separators']:,}")
    print(f"hard pairs = {len(hard):,}")
    print(f"search time = {search_seconds:.2f}s")
    print(f"total time = {total_seconds:.2f}s")

    print()
    print("===== TOP 20 =====")

    for rank, row in enumerate(ranking[:20], 1):
        print(
            f"{rank:2d}. separators={row['separators']:,} "
            f"indist={row['indistinguishable']:,}"
        )
        print(f"    mutations={row['mutations']}")
        print(f"    u={row['u']}")
        print(f"    v={row['v']}")

    if hard:
        print()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ZERO-SEPARATOR CANDIDATE FOUND")
        print("Independent verification required.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        for row in hard:
            print("u =", row["u"])
            print("v =", row["v"])


if __name__ == "__main__":
    main()
