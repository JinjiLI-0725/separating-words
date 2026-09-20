#!/usr/bin/env python3

from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import numpy as np

from separating_words.canonical_generator import generate_canonical_dfas


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

CHECKPOINT = RESULTS / "v4_5_beam_checkpoint.json"
OUTPUT = RESULTS / "v4_5_beam.json"

N = 47
EXPECTED_AUTOMATA = 166_152

SEED_U = "10101010101010101010101010101101010101001010101"
SEED_V = "10101101010101001010101010101010101010101010101"

assert len(SEED_U) == len(SEED_V) == N


def flip_many(word, positions):
    chars = list(word)
    for i in positions:
        chars[i] = "1" if chars[i] == "0" else "0"
    return "".join(chars)


def materialize_automata():
    rows = []
    counts = {}

    for k in range(1, 6):
        count = 0
        for transitions in generate_canonical_dfas(k):
            padded = list(transitions)

            # Safe: padded states are unreachable from state 0
            # for a k-state accessible DFA.
            for q in range(k, 5):
                padded.append((q, q))

            rows.append(padded)
            count += 1

        counts[k] = count
        print(f"loaded k={k}: {count:,}", flush=True)

    T = np.asarray(rows, dtype=np.uint8)

    if T.shape != (EXPECTED_AUTOMATA, 5, 2):
        raise RuntimeError(f"unexpected automata shape: {T.shape}")

    print(f"automata shape = {T.shape}", flush=True)
    print(f"automata memory = {T.nbytes / 1024**2:.2f} MB", flush=True)

    return T, counts


def encode_words(words):
    return np.asarray(
        [[ord(c) - 48 for c in w] for w in words],
        dtype=np.uint8,
    )


def endpoint_matrix_subset(T, words, automata_indices,
                           automata_batch=4096, word_batch=128):
    """
    Endpoint matrix for a selected set of automata.

    Returns shape:
        (number_of_words, number_of_selected_automata)
    """
    words = list(words)

    if len(words) == 0:
        return np.empty((0, len(automata_indices)), dtype=np.uint8)

    idx = np.asarray(automata_indices, dtype=np.int64)
    Ts = T[idx]

    bits = encode_words(words)

    W, length = bits.shape
    A = Ts.shape[0]

    out = np.empty((W, A), dtype=np.uint8)

    for a0 in range(0, A, automata_batch):
        a1 = min(a0 + automata_batch, A)

        tb = Ts[a0:a1]
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


def endpoint_matrix_all(T, words,
                        automata_batch=4096, word_batch=128):
    return endpoint_matrix_subset(
        T,
        words,
        np.arange(T.shape[0]),
        automata_batch=automata_batch,
        word_batch=word_batch,
    )


def score_pairs_from_endpoints(E, word_index, pairs):
    scores = np.empty(len(pairs), dtype=np.int32)

    for i, (u, v) in enumerate(pairs):
        scores[i] = np.count_nonzero(
            E[word_index[u]] != E[word_index[v]]
        )

    return scores


def score_pairs_subset(T, pairs, automata_indices):
    """
    Vectorized scoring against a witness pool.
    """
    if len(automata_indices) == 0:
        return np.zeros(len(pairs), dtype=np.int32)

    words = sorted({w for u, v in pairs for w in (u, v)})
    word_index = {w: i for i, w in enumerate(words)}

    E = endpoint_matrix_subset(
        T,
        words,
        automata_indices,
        automata_batch=4096,
        word_batch=256,
    )

    return score_pairs_from_endpoints(E, word_index, pairs)


def full_score_pairs(T, pairs):
    """
    Exact score against all 166,152 canonical <=5-state structures.
    Also returns the exact witness indices for every pair.
    """
    words = sorted({w for u, v in pairs for w in (u, v)})
    word_index = {w: i for i, w in enumerate(words)}

    print(
        f"  full scoring {len(pairs):,} candidates "
        f"using {len(words):,} unique words",
        flush=True,
    )

    t0 = time.time()

    E = endpoint_matrix_all(
        T,
        words,
        automata_batch=4096,
        word_batch=128,
    )

    print(
        f"  endpoint matrix {E.shape}, "
        f"{E.nbytes / 1024**2:.1f} MB, "
        f"{time.time() - t0:.2f}s",
        flush=True,
    )

    results = []

    for u, v in pairs:
        mask = E[word_index[u]] != E[word_index[v]]
        witness_indices = np.flatnonzero(mask)

        results.append(
            {
                "u": u,
                "v": v,
                "full_score": int(len(witness_indices)),
                "witness_indices": witness_indices.tolist(),
            }
        )

    return results


def generate_mutations(u, v):
    """
    Structured neighborhood around one parent.

    Includes:
      1. parent itself
      2. one coordinated +24 flip
      3. two coordinated +24 flips
      4. one same-position flip
      5. two same-position flips
      6. selected cross-offset combinations

    The search is intentionally structured rather than random.
    """
    candidates = {}

    def add(a, b, mutation):
        if a == b:
            return

        candidates.setdefault(
            (a, b),
            [],
        ).append(mutation)

    add(u, v, {"type": "parent"})

    # ---------------------------------------------------------
    # +24 aligned positions
    # u[i] corresponds heuristically to v[i-24].
    # ---------------------------------------------------------
    aligned = [(i, i - 24) for i in range(24, 47)]

    for ui, vi in aligned:
        add(
            flip_many(u, (ui,)),
            flip_many(v, (vi,)),
            {
                "type": "offset24_1",
                "u_positions": [ui],
                "v_positions": [vi],
            },
        )

    for (ui1, vi1), (ui2, vi2) in itertools.combinations(aligned, 2):
        add(
            flip_many(u, (ui1, ui2)),
            flip_many(v, (vi1, vi2)),
            {
                "type": "offset24_2",
                "u_positions": [ui1, ui2],
                "v_positions": [vi1, vi2],
            },
        )

    # ---------------------------------------------------------
    # Same-position mutations.
    # ---------------------------------------------------------
    for i in range(N):
        add(
            flip_many(u, (i,)),
            flip_many(v, (i,)),
            {
                "type": "same_1",
                "u_positions": [i],
                "v_positions": [i],
            },
        )

    for i, j in itertools.combinations(range(N), 2):
        add(
            flip_many(u, (i, j)),
            flip_many(v, (i, j)),
            {
                "type": "same_2",
                "u_positions": [i, j],
                "v_positions": [i, j],
            },
        )

    # ---------------------------------------------------------
    # Cross-offset mutations:
    # one aligned flip plus one same-position flip.
    # ---------------------------------------------------------
    for ui, vi in aligned:
        for p in range(N):
            add(
                flip_many(u, (ui, p)),
                flip_many(v, (vi, p)),
                {
                    "type": "offset24_plus_same",
                    "u_positions": [ui, p],
                    "v_positions": [vi, p],
                },
            )

    return candidates


def select_diverse(rows, beam_width):
    """
    Keep low scores while avoiding a beam made entirely of duplicates.
    """
    rows = sorted(
        rows,
        key=lambda r: (
            r["full_score"],
            r["u"],
            r["v"],
        ),
    )

    selected = []
    seen_pairs = set()
    seen_witness_sets = set()

    # First pass: prefer different witness sets.
    for row in rows:
        pair = (row["u"], row["v"])
        ws = tuple(row["witness_indices"])

        if pair in seen_pairs or ws in seen_witness_sets:
            continue

        selected.append(row)
        seen_pairs.add(pair)
        seen_witness_sets.add(ws)

        if len(selected) >= beam_width:
            return selected

    # Second pass: fill remaining slots by score.
    for row in rows:
        pair = (row["u"], row["v"])

        if pair in seen_pairs:
            continue

        selected.append(row)
        seen_pairs.add(pair)

        if len(selected) >= beam_width:
            break

    return selected


def save_checkpoint(generation, beam, best_ever, history, counts):
    payload = {
        "version": "V4.5",
        "generation": generation,
        "automata_count": EXPECTED_AUTOMATA,
        "counts_by_k": counts,
        "beam": beam,
        "best_ever": best_ever,
        "history": history,
        "timestamp": time.time(),
    }

    tmp = CHECKPOINT.with_suffix(".json.tmp")

    tmp.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    tmp.replace(CHECKPOINT)


def load_checkpoint():
    if not CHECKPOINT.exists():
        return None

    return json.loads(CHECKPOINT.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--generations", type=int, default=12)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--full-finalists", type=int, default=40)
    parser.add_argument("--resume", action="store_true")

    args = parser.parse_args()

    started = time.time()

    print("===== V4.5 COUNTEREXAMPLE-GUIDED BEAM SEARCH =====")
    print(f"generations     = {args.generations}")
    print(f"beam width      = {args.beam_width}")
    print(f"full finalists  = {args.full_finalists}")
    print(flush=True)

    T, counts = materialize_automata()

    checkpoint = load_checkpoint() if args.resume else None

    if checkpoint:
        generation_start = checkpoint["generation"] + 1
        beam = checkpoint["beam"]
        best_ever = checkpoint["best_ever"]
        history = checkpoint["history"]

        print(
            f"resuming after generation "
            f"{checkpoint['generation']}",
            flush=True,
        )
        print(
            f"best score so far = "
            f"{best_ever['full_score']}",
            flush=True,
        )

    else:
        print()
        print("===== INITIAL EXACT SCORE =====", flush=True)

        initial = full_score_pairs(
            T,
            [(SEED_U, SEED_V)],
        )[0]

        if initial["full_score"] != 52:
            raise RuntimeError(
                f"seed regression failed: "
                f"{initial['full_score']} != 52"
            )

        print("seed regression passed: score=52", flush=True)

        initial["generation"] = 0
        initial["parent_score"] = None
        initial["mutation"] = {"type": "seed"}

        beam = [initial]
        best_ever = dict(initial)

        history = [
            {
                "generation": 0,
                "best_score": 52,
                "beam_scores": [52],
            }
        ]

        generation_start = 1

        save_checkpoint(
            0,
            beam,
            best_ever,
            history,
            counts,
        )

    # =========================================================
    # Generational search
    # =========================================================

    for generation in range(
        generation_start,
        args.generations + 1,
    ):
        gen_started = time.time()

        print()
        print("=" * 60)
        print(f"GENERATION {generation}")
        print("=" * 60, flush=True)

        # -----------------------------------------------------
        # Generate candidates from every beam parent.
        # -----------------------------------------------------
        candidate_map = {}

        for parent_id, parent in enumerate(beam):
            u = parent["u"]
            v = parent["v"]

            local = generate_mutations(u, v)

            print(
                f"parent {parent_id}: "
                f"score={parent['full_score']} "
                f"generated={len(local):,}",
                flush=True,
            )

            for pair, mutations in local.items():
                entry = candidate_map.setdefault(
                    pair,
                    {
                        "parents": [],
                        "mutations": [],
                    },
                )

                entry["parents"].append(
                    {
                        "parent_id": parent_id,
                        "parent_score": parent["full_score"],
                    }
                )

                entry["mutations"].extend(mutations)

        candidate_pairs = list(candidate_map)

        print(
            f"unique generation candidates = "
            f"{len(candidate_pairs):,}",
            flush=True,
        )

        # -----------------------------------------------------
        # Union of current beam witnesses.
        # This is the cheap counterexample pool.
        # -----------------------------------------------------
        witness_pool = sorted(
            {
                idx
                for parent in beam
                for idx in parent["witness_indices"]
            }
        )

        print(
            f"active witness pool = "
            f"{len(witness_pool):,}",
            flush=True,
        )

        t0 = time.time()

        cheap_scores = score_pairs_subset(
            T,
            candidate_pairs,
            witness_pool,
        )

        print(
            f"cheap vectorized scoring = "
            f"{time.time() - t0:.2f}s",
            flush=True,
        )

        order = np.argsort(cheap_scores, kind="stable")

        # Keep enough cheap finalists to allow diversity.
        take = min(args.full_finalists, len(order))
        finalist_indices = order[:take]

        finalists = [
            candidate_pairs[int(i)]
            for i in finalist_indices
        ]

        print(
            "cheap best scores =",
            [
                int(cheap_scores[int(i)])
                for i in finalist_indices[:20]
            ],
            flush=True,
        )

        zero_pool = int(np.count_nonzero(cheap_scores == 0))

        print(
            f"zero against active witness pool = "
            f"{zero_pool:,}",
            flush=True,
        )

        # -----------------------------------------------------
        # Exact full scoring.
        # -----------------------------------------------------
        exact = full_score_pairs(T, finalists)

        enriched = []

        for local_index, row in enumerate(exact):
            pair = (row["u"], row["v"])
            original_idx = int(finalist_indices[local_index])

            meta = candidate_map[pair]

            row["cheap_score"] = int(
                cheap_scores[original_idx]
            )
            row["generation"] = generation
            row["parents"] = meta["parents"]
            row["mutations"] = meta["mutations"]

            enriched.append(row)

        enriched.sort(key=lambda r: r["full_score"])

        print()
        print("generation exact top:")
        for rank, row in enumerate(enriched[:10], 1):
            print(
                f"{rank:2d}. full={row['full_score']:,} "
                f"cheap={row['cheap_score']:,}",
                flush=True,
            )
            print(
                f"    mutation={row['mutations'][0]}",
                flush=True,
            )

        # -----------------------------------------------------
        # HARD PAIR?
        # -----------------------------------------------------
        hard = [
            row for row in enriched
            if row["full_score"] == 0
        ]

        if hard:
            winner = hard[0]

            print()
            print("!" * 68)
            print("FULL SCORE ZERO FOUND")
            print("STOPPING SEARCH IMMEDIATELY")
            print("INDEPENDENT VERIFICATION REQUIRED")
            print("!" * 68)
            print("u =", winner["u"])
            print("v =", winner["v"])
            print(flush=True)

            if best_ever["full_score"] != 0:
                best_ever = dict(winner)

            history.append(
                {
                    "generation": generation,
                    "best_score": 0,
                    "beam_scores": [r["full_score"] for r in enriched],
                    "zero_active_witness_candidates": zero_pool,
                }
            )

            beam = [winner]

            save_checkpoint(
                generation,
                beam,
                best_ever,
                history,
                counts,
            )

            OUTPUT.write_text(
                json.dumps(
                    {
                        "status": "ZERO_FOUND_NEEDS_VERIFICATION",
                        "winner": winner,
                        "best_ever": best_ever,
                        "history": history,
                        "elapsed_seconds": time.time() - started,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            return

        # -----------------------------------------------------
        # Update global champion.
        # -----------------------------------------------------
        if enriched[0]["full_score"] < best_ever["full_score"]:
            best_ever = dict(enriched[0])

            print()
            print(
                f"*** NEW GLOBAL BEST: "
                f"{best_ever['full_score']} ***",
                flush=True,
            )

        # -----------------------------------------------------
        # Preserve old beam members as candidates too.
        #
        # This is important: beam search is allowed to move
        # uphill, but we never lose the best states already found.
        # -----------------------------------------------------
        pool = enriched + beam

        beam = select_diverse(
            pool,
            args.beam_width,
        )

        beam.sort(key=lambda r: r["full_score"])

        history.append(
            {
                "generation": generation,
                "best_score": best_ever["full_score"],
                "generation_best": enriched[0]["full_score"],
                "beam_scores": [
                    row["full_score"]
                    for row in beam
                ],
                "active_witness_pool": len(witness_pool),
                "candidate_count": len(candidate_pairs),
                "zero_active_witness_candidates": zero_pool,
                "seconds": time.time() - gen_started,
            }
        )

        save_checkpoint(
            generation,
            beam,
            best_ever,
            history,
            counts,
        )

        print()
        print(
            f"beam scores -> "
            f"{[r['full_score'] for r in beam]}",
            flush=True,
        )
        print(
            f"best ever -> {best_ever['full_score']}",
            flush=True,
        )
        print(
            f"generation time -> "
            f"{time.time() - gen_started:.2f}s",
            flush=True,
        )
        print(
            f"checkpoint -> {CHECKPOINT}",
            flush=True,
        )

    # =========================================================
    # Normal completion
    # =========================================================

    elapsed = time.time() - started

    payload = {
        "status": "COMPLETED",
        "generations": args.generations,
        "beam_width": args.beam_width,
        "full_finalists": args.full_finalists,
        "best_ever": best_ever,
        "final_beam": beam,
        "history": history,
        "elapsed_seconds": elapsed,
    }

    OUTPUT.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("V4.5 COMPLETE")
    print("=" * 60)
    print(f"best full score = {best_ever['full_score']}")
    print(f"u = {best_ever['u']}")
    print(f"v = {best_ever['v']}")
    print(f"elapsed = {elapsed:.2f}s")
    print(f"saved -> {OUTPUT}")


if __name__ == "__main__":
    main()
