"""Automated Separating Words research runner."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from separating_words.canonical_generator import generate_canonical_dfas
from separating_words.separator import find_separator


RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

CHECKPOINT = RESULTS / "search_checkpoint.json"
RECORDS = RESULTS / "search_records.jsonl"

MAX_STATES = 5


def log(message):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[{stamp}] {message}", flush=True)


def save_checkpoint(data):
    tmp = CHECKPOINT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(CHECKPOINT)


def fingerprint(automata):
    h = hashlib.sha256()
    for transitions in automata:
        h.update(repr(transitions).encode())
        h.update(b"\n")
    return h.hexdigest()


def main():
    log("Separating Words automated runner starting")

    # ---------------------------------------------------------
    # Phase 1: build + fingerprint canonical DFA collections
    # ---------------------------------------------------------

    known = {}

    for k in range(1, MAX_STATES + 1):
        start = time.perf_counter()
        automata = list(generate_canonical_dfas(k))
        elapsed = time.perf_counter() - start

        known[k] = automata

        log(
            f"DFA k={k}: count={len(automata):,} "
            f"time={elapsed:.3f}s "
            f"sha256={fingerprint(automata)}"
        )

    # ---------------------------------------------------------
    # Phase 2: sanity certificate
    # ---------------------------------------------------------

    cert = find_separator("1000", "0010", MAX_STATES)

    if cert is None or cert.states != 3:
        raise RuntimeError("sanity certificate failed")

    log("Sanity check passed: sep(1000,0010)=3")

    # ---------------------------------------------------------
    # Phase 3:
    # Initial hard-pair reconnaissance.
    #
    # For each length n, group words by their complete endpoint
    # signature across all <= MAX_STATES automata.
    #
    # Equal signatures => no DFA in our database separates them.
    #
    # We intentionally begin with modest n. Later we will replace
    # this reference implementation with a memory-efficient search.
    # ---------------------------------------------------------

    all_automata = []

    for k in range(1, MAX_STATES + 1):
        all_automata.extend(known[k])

    log(f"Total automata loaded: {len(all_automata):,}")

    # Start small. This is reconnaissance, not yet the N(5) search.
    for n in range(1, 13):
        start = time.perf_counter()

        signatures = {}
        collision = None

        for value in range(1 << n):
            word = format(value, f"0{n}b")

            endpoint_signature = []

            for transitions in all_automata:
                state = 0

                for symbol in word:
                    state = transitions[state][int(symbol)]

                endpoint_signature.append(state)

            signature = bytes(endpoint_signature)

            previous = signatures.get(signature)

            if previous is not None and previous != word:
                collision = (previous, word)
                break

            signatures[signature] = word

        elapsed = time.perf_counter() - start

        checkpoint = {
            "phase": "reconnaissance",
            "max_states": MAX_STATES,
            "length": n,
            "words_checked": len(signatures),
            "collision": collision,
            "elapsed_seconds": elapsed,
        }

        save_checkpoint(checkpoint)

        log(
            f"n={n}: checked={len(signatures):,} "
            f"time={elapsed:.2f}s "
            f"collision={collision}"
        )

        if collision is not None:
            x, y = collision

            record = {
                "length": n,
                "max_states": MAX_STATES,
                "x": x,
                "y": y,
            }

            with RECORDS.open("a") as f:
                f.write(json.dumps(record) + "\n")

            log(f"HARD PAIR FOUND: x={x} y={y}")
            log("Stopping for independent verification.")
            return

    log("Reconnaissance completed through n=12 with no collision.")


if __name__ == "__main__":
    main()
