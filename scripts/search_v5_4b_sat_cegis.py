#!/usr/bin/env python3

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from pysat.formula import IDPool
from pysat.solvers import Solver

from separating_words.canonical_generator import generate_canonical_dfas


N = 47
MAX_STATES = 5

DEFAULT_BATCH_SIZE = 32
DEFAULT_MAX_ITERATIONS = 100

RESULT_PATH = Path("results/v5_4b_sat_cegis.json")


# ============================================================
# DFA materialization
# ============================================================

def load_all_dfas():
    """
    Load every canonical accessible DFA with <=5 states.

    For the NumPy verifier we pad smaller DFAs to 5 states.
    Padding is safe because states outside the real DFA are
    unreachable from start state 0.
    """
    raw = []
    padded = []
    sizes = []

    counts = {}

    for k in range(1, MAX_STATES + 1):
        count = 0

        for t in generate_canonical_dfas(k):
            t = tuple(tuple(row) for row in t)

            raw.append(t)
            sizes.append(k)

            p = np.zeros((MAX_STATES, 2), dtype=np.uint8)

            for q in range(k):
                p[q, 0] = t[q][0]
                p[q, 1] = t[q][1]

            # Unreachable padding states self-loop.
            for q in range(k, MAX_STATES):
                p[q, 0] = q
                p[q, 1] = q

            padded.append(p)

            count += 1

        counts[k] = count

    T = np.stack(padded, axis=0)

    return raw, np.asarray(sizes, dtype=np.uint8), T, counts


# ============================================================
# Fast exact verifier
# ============================================================

def endpoints_for_word(T, word):
    """
    Evaluate one word on all DFAs simultaneously.

    T shape:
        (num_automata, 5, 2)
    """
    m = T.shape[0]

    states = np.zeros(m, dtype=np.uint8)
    rows = np.arange(m)

    for ch in word:
        states = T[rows, states, int(ch)]

    return states


def find_separators(T, u, v):
    eu = endpoints_for_word(T, u)
    ev = endpoints_for_word(T, v)

    return np.flatnonzero(eu != ev), eu, ev


# ============================================================
# SAT encoding
# ============================================================

def add_exactly_one(solver, lits):
    solver.add_clause(lits)

    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            solver.add_clause([-lits[i], -lits[j]])


def add_dfa_constraint(
    solver,
    pool,
    dfa,
    constraint_id,
    xvars,
    yvars,
):
    """
    Add:
        delta_A(0,x) == delta_A(0,y)

    using one-hot state trajectories.
    """
    k = len(dfa)

    sx = [
        [
            pool.id(("sx", constraint_id, p, q))
            for q in range(k)
        ]
        for p in range(N + 1)
    ]

    sy = [
        [
            pool.id(("sy", constraint_id, p, q))
            for q in range(k)
        ]
        for p in range(N + 1)
    ]

    for p in range(N + 1):
        add_exactly_one(solver, sx[p])
        add_exactly_one(solver, sy[p])

    # Start state.
    solver.add_clause([sx[0][0]])
    solver.add_clause([sy[0][0]])

    for p in range(N):
        xb = xvars[p]
        yb = yvars[p]

        for q in range(k):
            r0, r1 = dfa[q]

            # x transition
            solver.add_clause([
                -sx[p][q],
                xb,
                sx[p + 1][r0],
            ])

            solver.add_clause([
                -sx[p][q],
                -xb,
                sx[p + 1][r1],
            ])

            # y transition
            solver.add_clause([
                -sy[p][q],
                yb,
                sy[p + 1][r0],
            ])

            solver.add_clause([
                -sy[p][q],
                -yb,
                sy[p + 1][r1],
            ])

    # Equal final state.
    for q in range(k):
        solver.add_clause([
            -sx[N][q],
            sy[N][q],
        ])

        solver.add_clause([
            -sy[N][q],
            sx[N][q],
        ])


def initialize_solver():
    pool = IDPool()

    xvars = [
        pool.id(("x", i))
        for i in range(N)
    ]

    yvars = [
        pool.id(("y", i))
        for i in range(N)
    ]

    solver = Solver(name="glucose4")

    # Lightweight alphabet-complement symmetry break.
    solver.add_clause([-xvars[0]])

    # Require x != y.
    diffs = []

    for i in range(N):
        d = pool.id(("diff", i))
        diffs.append(d)

        x = xvars[i]
        y = yvars[i]

        # d <-> x XOR y
        solver.add_clause([-d, x, y])
        solver.add_clause([-d, -x, -y])
        solver.add_clause([d, -x, y])
        solver.add_clause([d, x, -y])

    solver.add_clause(diffs)

    return solver, pool, xvars, yvars


def decode_word(model_positive, variables):
    return "".join(
        "1" if v in model_positive else "0"
        for v in variables
    )


# ============================================================
# Counterexample selection
# ============================================================

def structural_signature(dfa):
    """
    Cheap diversity signature.

    We deliberately do NOT require the selected counterexamples
    to have unique signatures. This is only used to spread the
    batch across structurally different DFAs when possible.
    """
    k = len(dfa)

    map0 = tuple(row[0] for row in dfa)
    map1 = tuple(row[1] for row in dfa)

    indeg0 = [0] * k
    indeg1 = [0] * k

    for q in map0:
        indeg0[q] += 1

    for q in map1:
        indeg1[q] += 1

    image0 = len(set(map0))
    image1 = len(set(map1))

    return (
        k,
        image0,
        image1,
        tuple(sorted(indeg0)),
        tuple(sorted(indeg1)),
    )


def select_counterexamples(
    separator_indices,
    raw_dfas,
    sizes,
    eu,
    ev,
    already_active,
    batch_size,
):
    """
    Greedy diversity selection.

    Pass 1:
        prefer different combinations of
        structural signature + endpoint pair.

    Pass 2:
        fill remaining slots with any unused separators.
    """
    candidates = [
        int(i)
        for i in separator_indices
        if int(i) not in already_active
    ]

    if not candidates:
        return []

    groups = defaultdict(list)

    for idx in candidates:
        dfa = raw_dfas[idx]

        key = (
            structural_signature(dfa),
            int(eu[idx]),
            int(ev[idx]),
        )

        groups[key].append(idx)

    selected = []

    # Round-robin across groups instead of taking the first
    # representative of every group in dictionary order.
    group_lists = list(groups.values())

    pos = 0

    while len(selected) < batch_size:
        added = False

        for group in group_lists:
            if pos < len(group):
                selected.append(group[pos])
                added = True

                if len(selected) >= batch_size:
                    break

        if not added:
            break

        pos += 1

    # Fill if diversity groups did not produce enough.
    selected_set = set(selected)

    if len(selected) < batch_size:
        for idx in candidates:
            if idx not in selected_set:
                selected.append(idx)
                selected_set.add(idx)

                if len(selected) >= batch_size:
                    break

    return selected


# ============================================================
# Checkpoint
# ============================================================

def save_checkpoint(
    status,
    start_time,
    active_indices,
    history,
    best,
):
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": "v5.4b",
        "status": status,
        "word_length": N,
        "active_constraints": active_indices,
        "active_constraint_count": len(active_indices),
        "history": history,
        "best": best,
        "elapsed_seconds": time.perf_counter() - start_time,
    }

    tmp = RESULT_PATH.with_suffix(".tmp")

    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)

    tmp.replace(RESULT_PATH)


# ============================================================
# Main CEGIS loop
# ============================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
    )

    args = parser.parse_args()

    start_time = time.perf_counter()

    print("===== V5.4B SAT CEGIS =====")
    print("word length =", N)
    print("batch size =", args.batch_size)
    print("max iterations =", args.max_iterations)
    print()

    print("Loading canonical DFAs...")

    load_start = time.perf_counter()

    raw_dfas, sizes, T, counts = load_all_dfas()

    print("canonical counts =", counts)
    print("total automata =", len(raw_dfas))
    print("transition tensor =", T.shape, T.dtype)
    print(
        "load time =",
        f"{time.perf_counter() - load_start:.2f}s",
    )
    print()

    if len(raw_dfas) != 166_152:
        raise RuntimeError(
            f"expected 166152 automata, got {len(raw_dfas)}"
        )

    solver, pool, xvars, yvars = initialize_solver()

    active_indices = []
    active_set = set()

    history = []

    best = {
        "separator_count": len(raw_dfas) + 1,
        "u": None,
        "v": None,
        "iteration": None,
    }

    try:
        for iteration in range(1, args.max_iterations + 1):

            print("=" * 70)
            print("ITERATION", iteration)
            print(
                "active DFA constraints =",
                len(active_indices),
            )
            print("SAT variables =", pool.top)

            solve_start = time.perf_counter()

            sat = solver.solve()

            solve_seconds = (
                time.perf_counter() - solve_start
            )

            print(
                "solver status =",
                "SAT" if sat else "UNSAT",
                f"({solve_seconds:.3f}s)",
            )

            if not sat:
                print()
                print(
                    "UNSAT: accumulated real DFA constraints "
                    "rule out every distinct length-47 pair."
                )

                save_checkpoint(
                    "UNSAT",
                    start_time,
                    active_indices,
                    history,
                    best,
                )

                return

            model_positive = {
                lit
                for lit in solver.get_model()
                if lit > 0
            }

            u = decode_word(
                model_positive,
                xvars,
            )

            v = decode_word(
                model_positive,
                yvars,
            )

            if u == v:
                raise RuntimeError(
                    "SAT encoding error: decoded words are equal"
                )

            print("u =", u)
            print("v =", v)

            verify_start = time.perf_counter()

            separators, eu, ev = find_separators(
                T,
                u,
                v,
            )

            verify_seconds = (
                time.perf_counter() - verify_start
            )

            separator_count = len(separators)

            print(
                "full verifier: separators =",
                f"{separator_count:,}",
                f"time={verify_seconds:.3f}s",
            )

            if separator_count < best["separator_count"]:
                best = {
                    "separator_count": separator_count,
                    "u": u,
                    "v": v,
                    "iteration": iteration,
                }

                print(
                    "*** NEW BEST:",
                    separator_count,
                    "separators ***",
                )

            entry = {
                "iteration": iteration,
                "active_constraint_count": len(
                    active_indices
                ),
                "sat_variables": pool.top,
                "solve_seconds": solve_seconds,
                "verify_seconds": verify_seconds,
                "separator_count": separator_count,
                "u": u,
                "v": v,
            }

            # Exact success.
            if separator_count == 0:
                history.append(entry)

                save_checkpoint(
                    "FOUND",
                    start_time,
                    active_indices,
                    history,
                    best,
                )

                print()
                print("=" * 70)
                print("CANDIDATE FOUND")
                print("=" * 70)
                print("u =", u)
                print("v =", v)
                print(
                    "No canonical <=5-state DFA "
                    "separates this pair."
                )
                print()
                print(
                    "IMPORTANT: independently verify "
                    "before making any mathematical claim."
                )

                return

            selected = select_counterexamples(
                separators,
                raw_dfas,
                sizes,
                eu,
                ev,
                active_set,
                args.batch_size,
            )

            entry["selected_counterexamples"] = selected
            entry["selected_count"] = len(selected)

            history.append(entry)

            if not selected:
                raise RuntimeError(
                    "model has separators but no new "
                    "counterexample DFA could be selected"
                )

            add_start = time.perf_counter()

            for idx in selected:
                constraint_id = len(active_indices)

                add_dfa_constraint(
                    solver,
                    pool,
                    raw_dfas[idx],
                    constraint_id,
                    xvars,
                    yvars,
                )

                active_indices.append(idx)
                active_set.add(idx)

            add_seconds = (
                time.perf_counter() - add_start
            )

            entry["add_seconds"] = add_seconds

            print(
                "added",
                len(selected),
                "counterexamples",
                f"({add_seconds:.3f}s)",
            )

            print(
                "active constraints now =",
                len(active_indices),
            )

            print(
                "best exact score so far =",
                best["separator_count"],
            )

            save_checkpoint(
                "RUNNING",
                start_time,
                active_indices,
                history,
                best,
            )

            # We don't forcibly kill Glucose mid-call here.
            # Instead stop before another iteration if the
            # previous solve has already exceeded our budget.
            if solve_seconds > 120:
                print()
                print(
                    "STOP: SAT solve exceeded 120 seconds."
                )

                save_checkpoint(
                    "SOLVE_LIMIT",
                    start_time,
                    active_indices,
                    history,
                    best,
                )

                return

        print()
        print(
            "Reached maximum iteration count:",
            args.max_iterations,
        )

        save_checkpoint(
            "MAX_ITERATIONS",
            start_time,
            active_indices,
            history,
            best,
        )

    finally:
        solver.delete()

    print()
    print("===== FINAL BEST =====")
    print("score =", best["separator_count"])
    print("iteration =", best["iteration"])
    print("u =", best["u"])
    print("v =", best["v"])
    print(
        "elapsed =",
        f"{time.perf_counter() - start_time:.2f}s",
    )


if __name__ == "__main__":
    main()
