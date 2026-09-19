import hashlib
import time

from separating_words.canonical_generator import generate_canonical_dfas


def fingerprint(automata):
    h = hashlib.sha256()

    for transitions in automata:
        h.update(repr(transitions).encode())
        h.update(b"\n")

    return h.hexdigest()


for k in range(1, 6):
    start = time.perf_counter()

    automata = list(generate_canonical_dfas(k))

    elapsed = time.perf_counter() - start

    print(
        f"k={k} "
        f"count={len(automata):,} "
        f"time={elapsed:.3f}s "
        f"sha256={fingerprint(automata)}"
    )
