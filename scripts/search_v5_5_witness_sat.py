#!/usr/bin/env python3

import json
import time
import threading
from pathlib import Path

import numpy as np
from pysat.formula import IDPool
from pysat.solvers import Solver

from separating_words.canonical_generator import generate_canonical_dfas


N = 47
MAX_STATES = 5
MAX_CANDIDATES = 1
SOLVE_TIMEOUT = 120

# V4.1 / V4.3 exact score-52 champion.
SEED_U = "10101010101010101010101010101101010101001010101"
SEED_V = "10101101010101001010101010101010101010101010101"

# Known V4.4 pair:
# globally separated by 64 DFAs, but fools all 52 seed witnesses.
WARM_U = "10101010101010101010101010101001011101001010101"
WARM_V = "10101001011101001010101010101010101010101010101"

RESULT_PATH = Path("results/v5_5_witness_sat.json")


def load_all_dfas():
    raw = []
    padded = []
    counts = {}

    for k in range(1, MAX_STATES + 1):
        count = 0

        for t in generate_canonical_dfas(k):
            t = tuple(tuple(row) for row in t)
            raw.append(t)

            p = np.zeros((MAX_STATES, 2), dtype=np.uint8)

            for q in range(MAX_STATES):
                p[q, 0] = q
                p[q, 1] = q

            for q in range(k):
                p[q, 0] = t[q][0]
                p[q, 1] = t[q][1]

            padded.append(p)
            count += 1

        counts[k] = count

    return raw, np.stack(padded), counts


def endpoints(T, word):
    m = len(T)
    rows = np.arange(m)
    states = np.zeros(m, dtype=np.uint8)

    for ch in word:
        states = T[rows, states, int(ch)]

    return states


def score_pair(T, u, v):
    eu = endpoints(T, u)
    ev = endpoints(T, v)
    separators = np.flatnonzero(eu != ev)
    return separators, eu, ev


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

    solver.add_clause([sx[0][0]])
    solver.add_clause([sy[0][0]])

    for p in range(N):
        xb = xvars[p]
        yb = yvars[p]

        for q in range(k):
            r0, r1 = dfa[q]

            solver.add_clause([
                -sx[p][q], xb, sx[p + 1][r0]
            ])
            solver.add_clause([
                -sx[p][q], -xb, sx[p + 1][r1]
            ])

            solver.add_clause([
                -sy[p][q], yb, sy[p + 1][r0]
            ])
            solver.add_clause([
                -sy[p][q], -yb, sy[p + 1][r1]
            ])

    for q in range(k):
        solver.add_clause([
            -sx[N][q], sy[N][q]
        ])
        solver.add_clause([
            -sy[N][q], sx[N][q]
        ])


def initialize_solver():
    pool = IDPool()

    xvars = [pool.id(("x", i)) for i in range(N)]
    yvars = [pool.id(("y", i)) for i in range(N)]

    solver = Solver(name="glucose4")

    # Safe global alphabet-complement symmetry break.
    solver.add_clause([-xvars[0]])

    # x != y
    diffs = []

    for i in range(N):
        d = pool.id(("diff", i))
        diffs.append(d)

        x = xvars[i]
        y = yvars[i]

        solver.add_clause([-d, x, y])
        solver.add_clause([-d, -x, -y])
        solver.add_clause([d, -x, y])
        solver.add_clause([d, x, -y])

    solver.add_clause(diffs)

    return solver, pool, xvars, yvars


def solve_with_timeout(solver, seconds):
    """
    Interrupt Glucose if the call exceeds the time budget.

    Returns:
        True  = SAT
        False = UNSAT
        None  = interrupted / timeout
    """
    timer = threading.Timer(seconds, solver.interrupt)
    timer.daemon = True
    timer.start()

    try:
        result = solver.solve_limited(
            expect_interrupt=True
        )
    finally:
        timer.cancel()
        solver.clear_interrupt()

    return result


def decode(model, variables):
    positive = {x for x in model if x > 0}

    return "".join(
        "1" if v in positive else "0"
        for v in variables
    )


def add_pair_blocking_clause(
    solver,
    u,
    v,
    xvars,
    yvars,
):
    """
    Block this exact ordered pair.

    At least one x/y bit must differ next time.
    """
    clause = []

    for bit, var in zip(u, xvars):
        clause.append(
            -var if bit == "1" else var
        )

    for bit, var in zip(v, yvars):
        clause.append(
            -var if bit == "1" else var
        )

    solver.add_clause(clause)


def save(payload):
    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp = RESULT_PATH.with_suffix(".tmp")

    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)

    tmp.replace(RESULT_PATH)


def main():
    start = time.perf_counter()

    print("===== V5.5 WITNESS-TARGETED SAT =====")
    print("length =", N)
    print("candidate cap =", MAX_CANDIDATES)
    print("SAT timeout =", SOLVE_TIMEOUT, "seconds")
    print()

    if len(SEED_U) != N or len(SEED_V) != N:
        raise RuntimeError("seed length mismatch")

    print("Loading all canonical DFAs...")

    raw, T, counts = load_all_dfas()

    print("counts =", counts)
    print("total =", len(raw))

    if len(raw) != 166_152:
        raise RuntimeError(
            f"expected 166152 DFAs, got {len(raw)}"
        )

    print()
    print("Recovering seed witnesses...")

    seed_sep, _, _ = score_pair(
        T,
        SEED_U,
        SEED_V,
    )

    witness_indices = [
        int(x) for x in seed_sep
    ]

    print("seed score =", len(witness_indices))

    if len(witness_indices) != 52:
        raise RuntimeError(
            "expected exact seed score 52, got "
            f"{len(witness_indices)}"
        )

    print(
        "witness state sizes =",
        sorted({
            len(raw[i])
            for i in witness_indices
        }),
    )

    # Regression check for the known V4.4 warm pair.
    warm_sep, _, _ = score_pair(
        T,
        WARM_U,
        WARM_V,
    )

    warm_sep_set = set(map(int, warm_sep))
    old52 = set(witness_indices)
    warm_old52 = old52.intersection(warm_sep_set)

    print("warm pair score =", len(warm_sep))
    print(
        "warm pair old-52 separators =",
        len(warm_old52),
    )

    if len(warm_sep) != 64 or warm_old52:
        raise RuntimeError(
            "warm-start pair regression failed"
        )

    solver, pool, xvars, yvars = (
        initialize_solver()
    )

    print()
    print("Adding all 52 witness constraints...")

    add_start = time.perf_counter()

    for cid, idx in enumerate(witness_indices):
        add_dfa_constraint(
            solver,
            pool,
            raw[idx],
            cid,
            xvars,
            yvars,
        )

    phase_lits = []

    for bit, var in zip(WARM_U, xvars):
        phase_lits.append(
            var if bit == "1" else -var
        )

    for bit, var in zip(WARM_V, yvars):
        phase_lits.append(
            var if bit == "1" else -var
        )

    solver.set_phases(phase_lits)

    print(
        "warm-start phases set from "
        "V4.4 score-64 pair"
    )

    print(
        "SAT variables =",
        pool.top,
    )
    print(
        "constraint build time =",
        f"{time.perf_counter() - add_start:.3f}s",
    )

    results = []
    best_score = 166_153
    best_pair = None
    status = "RUNNING"

    try:
        for candidate_no in range(
            1,
            MAX_CANDIDATES + 1,
        ):
            print()
            print("=" * 70)
            print("CANDIDATE", candidate_no)

            solve_start = time.perf_counter()

            sat = solve_with_timeout(
                solver,
                SOLVE_TIMEOUT,
            )

            solve_seconds = (
                time.perf_counter() - solve_start
            )

            if sat is None:
                print(
                    "TIMEOUT after",
                    f"{solve_seconds:.2f}s",
                )
                status = "TIMEOUT"
                break

            if sat is False:
                print(
                    "UNSAT under the 52 witness constraints"
                )
                status = "UNSAT"
                break

            print(
                "SAT solve =",
                f"{solve_seconds:.3f}s",
            )

            model = solver.get_model()

            u = decode(model, xvars)
            v = decode(model, yvars)

            print("u =", u)
            print("v =", v)

            verify_start = time.perf_counter()

            sep, _, _ = score_pair(T, u, v)

            verify_seconds = (
                time.perf_counter() - verify_start
            )

            score = len(sep)

            # Sanity check: every SAT model must fool
            # all 52 seed witnesses.
            seed_witness_survivors = sum(
                1
                for idx in witness_indices
                if idx in set(map(int, sep))
            )

            print(
                "global score =",
                f"{score:,}",
            )
            print(
                "old-52 separators =",
                seed_witness_survivors,
            )
            print(
                "verify =",
                f"{verify_seconds:.3f}s",
            )

            if seed_witness_survivors != 0:
                raise RuntimeError(
                    "SAT encoding verification failed: "
                    "candidate is separated by an asserted "
                    "seed witness"
                )

            if score < best_score:
                best_score = score
                best_pair = (u, v)

                print(
                    "*** NEW V5.5 BEST:",
                    score,
                    "***",
                )

            entry = {
                "candidate": candidate_no,
                "u": u,
                "v": v,
                "global_score": score,
                "solve_seconds": solve_seconds,
                "verify_seconds": verify_seconds,
            }

            results.append(entry)

            payload = {
                "version": "v5.5",
                "status": "RUNNING",
                "seed_u": SEED_U,
                "seed_v": SEED_V,
                "seed_score": 52,
                "witness_indices": witness_indices,
                "candidates": results,
                "best_score": best_score,
                "best_pair": best_pair,
                "elapsed_seconds":
                    time.perf_counter() - start,
            }

            save(payload)

            if score == 0:
                print()
                print("=" * 70)
                print("SCORE-ZERO CANDIDATE FOUND")
                print("=" * 70)
                print(
                    "STOP. Independent exhaustive "
                    "verification is required."
                )

                status = "FOUND"
                break

            # Ask for a genuinely different pair.
            add_pair_blocking_clause(
                solver,
                u,
                v,
                xvars,
                yvars,
            )

        else:
            status = "COMPLETE"

    finally:
        solver.delete()

    payload = {
        "version": "v5.5",
        "status": status,
        "seed_u": SEED_U,
        "seed_v": SEED_V,
        "seed_score": 52,
        "witness_indices": witness_indices,
        "candidates": results,
        "best_score": best_score,
        "best_pair": best_pair,
        "elapsed_seconds":
            time.perf_counter() - start,
    }

    save(payload)

    print()
    print("===== V5.5 SUMMARY =====")
    print("status =", status)
    print("candidates =", len(results))
    print("best score =", best_score)
    print("best pair =", best_pair)
    print(
        "elapsed =",
        f"{time.perf_counter() - start:.2f}s",
    )


if __name__ == "__main__":
    main()
