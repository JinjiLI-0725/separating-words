"""Vectorized Separating Words hard-pair search."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from separating_words.canonical_generator import generate_canonical_dfas


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

CHECKPOINT = RESULTS / "search_v2_checkpoint.json"
RECORDS = RESULTS / "search_v2_records.jsonl"

MAX_STATES = 5
MAX_LENGTH = 20


def log(msg):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[{stamp}] {msg}", flush=True)


def save_checkpoint(data):
    tmp = CHECKPOINT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(CHECKPOINT)


def build_transition_arrays():
    """Pack every canonical DFA with <=5 states into NumPy arrays."""

    automata = []

    for k in range(1, MAX_STATES + 1):
        autos = list(generate_canonical_dfas(k))
        log(f"k={k}: {len(autos):,} canonical automata")

        for transitions in autos:
            padded = list(transitions)

            # Unused states are harmless because they are unreachable.
            while len(padded) < MAX_STATES:
                padded.append((0, 0))

            automata.append(padded)

    arr = np.asarray(automata, dtype=np.uint8)

    delta0 = arr[:, :, 0]
    delta1 = arr[:, :, 1]

    return delta0, delta1


def step(states, delta):
    """Apply one symbol simultaneously to every DFA."""

    rows = np.arange(states.size)
    return delta[rows, states]


def signature_hash(states):
    return hashlib.blake2b(
        states.tobytes(),
        digest_size=16,
    ).digest()


def exact_verify(x, y, delta0, delta1):
    """Verify that x and y finish identically in every DFA."""

    sx = np.zeros(delta0.shape[0], dtype=np.uint8)
    sy = np.zeros(delta0.shape[0], dtype=np.uint8)

    for c in x:
        sx = step(sx, delta0 if c == "0" else delta1)

    for c in y:
        sy = step(sy, delta0 if c == "0" else delta1)

    return np.array_equal(sx, sy)


def main():
    log("Separating Words vectorized search v2 starting")

    start = time.perf_counter()
    delta0, delta1 = build_transition_arrays()
    build_time = time.perf_counter() - start

    count = delta0.shape[0]

    log(
        f"Loaded {count:,} automata "
        f"in {build_time:.2f}s"
    )

    # Root prefix: every automaton starts in state 0.
    frontier = {
        b"": np.zeros(count, dtype=np.uint8)
    }

    for n in range(1, MAX_LENGTH + 1):

        start = time.perf_counter()

        next_frontier = {}
        seen = {}

        collision = None

        for prefix, states in frontier.items():

            for symbol, delta in (
                (b"0", delta0),
                (b"1", delta1),
            ):
                word = prefix + symbol
                child = step(states, delta)

                digest = signature_hash(child)

                previous = seen.get(digest)

                if previous is not None:
                    prev_word, prev_states = previous

                    # Hash collision alone is NOT evidence.
                    # Require exact state-vector equality.
                    if np.array_equal(child, prev_states):
                        x = prev_word.decode()
                        y = word.decode()

                        if exact_verify(x, y, delta0, delta1):
                            collision = (x, y)
                            break

                else:
                    seen[digest] = (word, child)

                next_frontier[word] = child

            if collision:
                break

        elapsed = time.perf_counter() - start

        memory_mb = sum(
            states.nbytes
            for states in next_frontier.values()
        ) / (1024 * 1024)

        checkpoint = {
            "phase": "vectorized_search",
            "max_states": MAX_STATES,
            "length": n,
            "words": len(next_frontier),
            "collision": collision,
            "elapsed_seconds": elapsed,
            "frontier_memory_mb": memory_mb,
        }

        save_checkpoint(checkpoint)

        log(
            f"n={n}: words={len(next_frontier):,} "
            f"time={elapsed:.3f}s "
            f"frontier={memory_mb:.1f}MB "
            f"collision={collision}"
        )

        if collision:
            x, y = collision

            with RECORDS.open("a") as f:
                f.write(json.dumps({
                    "length": n,
                    "max_states": MAX_STATES,
                    "x": x,
                    "y": y,
                    "verified": True,
                }) + "\n")

            log(f"HARD PAIR FOUND: {x} / {y}")
            log("Exact verification passed.")
            return

        # Safety guard: this representation intentionally starts simple.
        # Don't let exponential frontier storage consume the server.
        if memory_mb > 1000:
            log("Memory safety limit reached.")
            log("Stopping cleanly before frontier becomes too large.")
            return

        frontier = next_frontier

    log(f"Completed through n={MAX_LENGTH}")


if __name__ == "__main__":
    main()
