#!/usr/bin/env python3

from collections import Counter, defaultdict
from separating_words.canonical_generator import generate_canonical_dfas

U = "10101010101010101010101010101101010101001010101"
V = "10101101010101001010101010101010101010101010101"


def run_trace(t, word):
    q = 0
    trace = [q]
    for b in word:
        q = t[q][int(b)]
        trace.append(q)
    return trace


def functional_signature(mapping):
    """
    Isomorphism-invariant coarse signature of one transition map:
    sorted cycle lengths + indegrees.
    """
    n = len(mapping)
    seen_cycles = set()
    cycle_lengths = []

    for start in range(n):
        path = []
        pos = {}
        q = start

        while q not in pos and q not in seen_cycles:
            pos[q] = len(path)
            path.append(q)
            q = mapping[q]

        if q in pos:
            cyc = path[pos[q]:]
            cycle_lengths.append(len(cyc))
            seen_cycles.update(cyc)

    indeg = [0] * n
    for q in mapping:
        indeg[q] += 1

    return (
        tuple(sorted(cycle_lengths)),
        tuple(sorted(indeg)),
    )


def scc_sizes(t):
    """Tiny Tarjan SCC implementation for the 2-letter transition graph."""
    n = len(t)
    index = 0
    stack = []
    onstack = set()
    idx = [-1] * n
    low = [0] * n
    sizes = []

    def visit(v):
        nonlocal index
        idx[v] = low[v] = index
        index += 1
        stack.append(v)
        onstack.add(v)

        for w in t[v]:
            if idx[w] == -1:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in onstack:
                low[v] = min(low[v], idx[w])

        if low[v] == idx[v]:
            size = 0
            while True:
                w = stack.pop()
                onstack.remove(w)
                size += 1
                if w == v:
                    break
            sizes.append(size)

    for v in range(n):
        if idx[v] == -1:
            visit(v)

    return tuple(sorted(sizes, reverse=True))


def divergence_signature(t):
    a = run_trace(t, U)
    b = run_trace(t, V)

    different = tuple(
        i for i in range(len(a))
        if a[i] != b[i]
    )

    first = different[0] if different else None
    last = different[-1] if different else None

    # Runs of consecutive positions at which the states differ.
    runs = []
    if different:
        start = prev = different[0]
        for x in different[1:]:
            if x != prev + 1:
                runs.append((start, prev))
                start = x
            prev = x
        runs.append((start, prev))

    return first, last, tuple(runs)


def main():
    witnesses = []

    counts = {}

    global_index = 0

    for k in range(1, 6):
        count = 0

        for t in generate_canonical_dfas(k):
            count += 1

            tu = run_trace(t, U)
            tv = run_trace(t, V)

            if tu[-1] != tv[-1]:
                witnesses.append((global_index, k, t, tu, tv))

            global_index += 1

        counts[k] = count

    print("===== V5.2 STRUCTURAL ANALYSIS =====")
    print("canonical counts:", counts)
    print("total:", global_index)
    print("witnesses:", len(witnesses))
    print()

    if global_index != 166_152:
        raise RuntimeError(
            f"Expected 166152 automata, got {global_index}"
        )

    if len(witnesses) != 52:
        raise RuntimeError(
            f"Expected 52 witnesses, got {len(witnesses)}"
        )

    family_counter = Counter()
    family_members = defaultdict(list)

    endpoint_counter = Counter()
    t0_counter = Counter()
    t1_counter = Counter()
    scc_counter = Counter()
    divergence_counter = Counter()

    for global_idx, k, t, tu, tv in witnesses:
        map0 = tuple(row[0] for row in t)
        map1 = tuple(row[1] for row in t)

        sig0 = functional_signature(map0)
        sig1 = functional_signature(map1)
        scc = scc_sizes(t)
        div = divergence_signature(t)

        endpoint = (tu[-1], tv[-1])

        # Coarse structural family.
        family = (
            sig0,
            sig1,
            scc,
            div[0],       # first divergence
            div[1],       # last divergence
            tuple(b-a+1 for a, b in div[2]),
        )

        family_counter[family] += 1
        family_members[family].append(
            {
                "index": global_idx,
                "transitions": t,
                "endpoint": endpoint,
                "runs": div[2],
            }
        )

        endpoint_counter[endpoint] += 1
        t0_counter[sig0] += 1
        t1_counter[sig1] += 1
        scc_counter[scc] += 1
        divergence_counter[div] += 1

    print("5-state witnesses:",
          sum(1 for _, k, *_ in witnesses if k == 5))
    print()

    print("===== ENDPOINT PAIRS =====")
    for key, n in endpoint_counter.most_common():
        print(f"{key}: {n}")

    print()
    print("===== T0 FUNCTION TYPES =====")
    for key, n in t0_counter.most_common():
        print(f"{n:>3}  {key}")

    print()
    print("===== T1 FUNCTION TYPES =====")
    for key, n in t1_counter.most_common():
        print(f"{n:>3}  {key}")

    print()
    print("===== SCC TYPES =====")
    for key, n in scc_counter.most_common():
        print(f"{n:>3}  {key}")

    print()
    print("===== EXACT DIVERGENCE PATTERNS =====")
    print("number of distinct patterns:", len(divergence_counter))

    for key, n in divergence_counter.most_common(15):
        first, last, runs = key
        print(
            f"{n:>3} | first={first:>2} last={last:>2} "
            f"| runs={runs}"
        )

    print()
    print("===== COARSE STRUCTURAL FAMILIES =====")
    print("number of families:", len(family_counter))

    ordered = family_counter.most_common()

    for rank, (family, n) in enumerate(ordered, 1):
        sig0, sig1, scc, first, last, run_lengths = family

        print()
        print(f"FAMILY {rank}: {n} witnesses")
        print("  T0:", sig0)
        print("  T1:", sig1)
        print("  SCC:", scc)
        print("  divergence:",
              f"first={first}, last={last}, run_lengths={run_lengths}")

        # Print up to three concrete representatives.
        for m in family_members[family][:3]:
            print(
                "   ",
                f"idx={m['index']}",
                f"endpoint={m['endpoint']}",
                f"T={m['transitions']}",
            )

    print()
    print("===== SUMMARY =====")
    print("witnesses =", len(witnesses))
    print("structural families =", len(family_counter))
    print(
        "largest family =",
        ordered[0][1] if ordered else 0,
    )


if __name__ == "__main__":
    main()
