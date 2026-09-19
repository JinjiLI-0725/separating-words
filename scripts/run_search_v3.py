#!/usr/bin/env python3
"""
Separating Words search v3.

Memory-efficient architecture:
- enumerate all canonical accessible DFAs with <= MAX_STATES states;
- process automata in chunks;
- process every word of a fixed length simultaneously;
- maintain only a compact 128-bit fingerprint per word;
- detect equal fingerprints;
- independently verify candidate collisions against every DFA.

A hash collision is NEVER accepted as a mathematical witness.
"""

import argparse
import hashlib
import json
import os
import resource
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from separating_words.canonical_generator import generate_canonical_dfas


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

MAX_STATES = 5

# Two independent 64-bit rolling fingerprints.
MASK64 = (1 << 64) - 1
P1 = np.uint64(0x9E3779B185EBCA87)
P2 = np.uint64(0xC2B2AE3D27D4EB4F)
C1 = np.uint64(0x165667B19E3779F9)
C2 = np.uint64(0x85EBCA77C2B2AE63)


def log(message):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[{stamp}] {message}", flush=True)


def rss_mb():
    # Linux ru_maxrss is KiB.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def save_checkpoint(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def all_automata():
    """Yield padded <=5-state transition tables."""
    for k in range(1, MAX_STATES + 1):
        count = 0

        for transitions in generate_canonical_dfas(k):
            padded = list(transitions)

            while len(padded) < MAX_STATES:
                padded.append((0, 0))

            count += 1
            yield tuple(padded)

        log(f"enumerated k={k}: {count:,}")


def chunked_automata(chunk_size):
    chunk = []

    for automaton in all_automata():
        chunk.append(automaton)

        if len(chunk) >= chunk_size:
            yield np.asarray(chunk, dtype=np.uint8)
            chunk = []

    if chunk:
        yield np.asarray(chunk, dtype=np.uint8)


def endpoint_matrix_for_chunk(n, transitions):
    """
    Compute endpoint states for every length-n binary word against one
    chunk of automata.

    Returns shape:
        (2**n, chunk_size)

    Row order is numeric binary word order:
        000..., ..., 111...
    """

    m = transitions.shape[0]

    # Start with the empty word.
    states = np.zeros((1, m), dtype=np.uint8)
    automata = np.arange(m)

    delta0 = transitions[:, :, 0]
    delta1 = transitions[:, :, 1]

    for _ in range(n):
        zero = delta0[automata, states]
        one = delta1[automata, states]

        # Numeric binary order:
        # existing prefixes followed by 0/1 as least-significant new branch.
        # Interleave children so row i corresponds to format(i, f"0{n}b").
        new_states = np.empty(
            (states.shape[0] * 2, m),
            dtype=np.uint8,
        )

        new_states[0::2] = zero
        new_states[1::2] = one

        states = new_states

    return states


def update_fingerprints(h1, h2, endpoints, chunk_index):
    """
    Fold a DFA chunk into two independent uint64 fingerprints.

    We deliberately incorporate columns sequentially. This preserves
    automaton order and avoids retaining endpoint data after this chunk.
    """

    salt1 = np.uint64((chunk_index + 1) * 0x100000001B3 & MASK64)
    salt2 = np.uint64((chunk_index + 1) * 0x9E3779B1 & MASK64)

    # endpoints[:, j] is one byte per word.
    for j in range(endpoints.shape[1]):
        x = endpoints[:, j].astype(np.uint64)

        with np.errstate(over="ignore"):
            h1 = h1 * P1 + x + C1 + salt1
            h2 = h2 * P2 + x + C2 + salt2

    return h1, h2


def word_from_id(value, n):
    return format(int(value), f"0{n}b")


def exact_equal(x_id, y_id, n, chunk_size):
    """Exact independent verification across every <=5-state DFA."""

    x = word_from_id(x_id, n)
    y = word_from_id(y_id, n)

    for transitions in chunked_automata(chunk_size):
        m = transitions.shape[0]
        automata = np.arange(m)

        sx = np.zeros(m, dtype=np.uint8)
        sy = np.zeros(m, dtype=np.uint8)

        for c in x:
            sx = transitions[automata, sx, int(c)]

        for c in y:
            sy = transitions[automata, sy, int(c)]

        if not np.array_equal(sx, sy):
            return False

    return True


def search_length(n, chunk_size):
    words = 1 << n

    h1 = np.zeros(words, dtype=np.uint64)
    h2 = np.zeros(words, dtype=np.uint64)

    total_automata = 0
    chunks = 0
    start = time.perf_counter()

    log(
        f"START n={n} words={words:,} "
        f"chunk_size={chunk_size:,}"
    )

    for chunk_index, transitions in enumerate(
        chunked_automata(chunk_size)
    ):
        chunks += 1
        total_automata += transitions.shape[0]

        endpoints = endpoint_matrix_for_chunk(n, transitions)

        h1, h2 = update_fingerprints(
            h1,
            h2,
            endpoints,
            chunk_index,
        )

        del endpoints
        del transitions

        if chunks % 10 == 0:
            log(
                f"n={n} chunks={chunks:,} "
                f"automata={total_automata:,} "
                f"rss_peak={rss_mb():.1f}MB"
            )

    # Lexicographically sort the 128-bit pair.
    order = np.lexsort((h2, h1))

    sorted_h1 = h1[order]
    sorted_h2 = h2[order]

    same = (
        (sorted_h1[1:] == sorted_h1[:-1])
        &
        (sorted_h2[1:] == sorted_h2[:-1])
    )

    positions = np.flatnonzero(same)

    elapsed = time.perf_counter() - start

    log(
        f"n={n} fingerprint pass complete: "
        f"automata={total_automata:,} "
        f"candidate_pairs={len(positions):,} "
        f"time={elapsed:.2f}s "
        f"rss_peak={rss_mb():.1f}MB"
    )

    verified = None

    for pos in positions:
        x_id = int(order[pos])
        y_id = int(order[pos + 1])

        x = word_from_id(x_id, n)
        y = word_from_id(y_id, n)

        log(f"candidate hash collision: {x} / {y}")

        if exact_equal(x_id, y_id, n, chunk_size):
            verified = (x, y)
            log(f"EXACT HARD PAIR VERIFIED: {x} / {y}")
            break

        log("candidate rejected by exact verification")

    return {
        "length": n,
        "words": words,
        "automata": total_automata,
        "candidate_pairs": int(len(positions)),
        "collision": verified,
        "elapsed_seconds": elapsed,
        "peak_rss_mb": rss_mb(),
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        type=int,
        default=13,
    )

    parser.add_argument(
        "--end",
        type=int,
        default=13,
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1024,
    )

    args = parser.parse_args()

    checkpoint = RESULTS / "search_v3_checkpoint.json"
    records = RESULTS / "search_v3_records.jsonl"

    log("===== SEPARATING WORDS V3 =====")
    log(
        f"lengths={args.start}..{args.end} "
        f"chunk_size={args.chunk_size}"
    )

    for n in range(args.start, args.end + 1):
        result = search_length(n, args.chunk_size)

        save_checkpoint(
            checkpoint,
            {
                "phase": "v3",
                **result,
            },
        )

        with records.open("a") as f:
            f.write(json.dumps(result) + "\n")

        if result["collision"] is not None:
            log("Stopping after verified hard pair.")
            return

    log("V3 requested range completed.")


if __name__ == "__main__":
    main()
