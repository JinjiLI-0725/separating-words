#!/usr/bin/env python3

import time
from pysat.formula import IDPool
from pysat.solvers import Solver

from separating_words.canonical_generator import generate_canonical_dfas

N = 47
LEVELS = [8, 16, 32, 64, 128, 256]


def load_5_state_dfas(limit):
    out = []
    for t in generate_canonical_dfas(5):
        out.append(tuple(tuple(x) for x in t))
        if len(out) >= limit:
            break
    return out


def add_exactly_one(solver, lits):
    # At least one.
    solver.add_clause(lits)

    # At most one.
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            solver.add_clause([-lits[i], -lits[j]])


def add_dfa_constraint(solver, pool, dfa, aidx, xvars, yvars):
    """
    Require this fixed DFA to end in the SAME state on x and y.

    One-hot state encoding:
        X[aidx,p,q] = state after first p bits of x is q
        Y[aidx,p,q] = state after first p bits of y is q
    """
    k = len(dfa)

    sx = [
        [pool.id(("sx", aidx, p, q)) for q in range(k)]
        for p in range(N + 1)
    ]

    sy = [
        [pool.id(("sy", aidx, p, q)) for q in range(k)]
        for p in range(N + 1)
    ]

    # Exactly one state at every position.
    for p in range(N + 1):
        add_exactly_one(solver, sx[p])
        add_exactly_one(solver, sy[p])

    # Start state = 0.
    solver.add_clause([sx[0][0]])
    solver.add_clause([sy[0][0]])

    # Fixed DFA transitions.
    #
    # If current state=q and bit=0 => next=T[q][0]
    # If current state=q and bit=1 => next=T[q][1]
    for p in range(N):
        xb = xvars[p]
        yb = yvars[p]

        for q in range(k):
            r0, r1 = dfa[q]

            # sx[p][q] AND not xb -> sx[p+1][r0]
            solver.add_clause([
                -sx[p][q],
                xb,
                sx[p + 1][r0],
            ])

            # sx[p][q] AND xb -> sx[p+1][r1]
            solver.add_clause([
                -sx[p][q],
                -xb,
                sx[p + 1][r1],
            ])

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

    # Final states must be equal.
    # With one-hot encoding:
    # sx[N][q] <-> sy[N][q]
    for q in range(k):
        solver.add_clause([-sx[N][q], sy[N][q]])
        solver.add_clause([-sy[N][q], sx[N][q]])


def decode_word(model_set, vars_):
    return "".join(
        "1" if v in model_set else "0"
        for v in vars_
    )


def run_level(dfas, level):
    pool = IDPool()

    xvars = [pool.id(("x", i)) for i in range(N)]
    yvars = [pool.id(("y", i)) for i in range(N)]

    build_start = time.perf_counter()

    with Solver(name="glucose4") as solver:

        # Alphabet-complement symmetry break, same idea as V5.1.
        solver.add_clause([-xvars[0]])

        # Require x != y:
        #
        # d_i <-> x_i XOR y_i
        # and OR_i d_i.
        diffs = []

        for i in range(N):
            d = pool.id(("diff", i))
            diffs.append(d)

            x = xvars[i]
            y = yvars[i]

            # d <-> XOR(x,y)
            solver.add_clause([-d, x, y])
            solver.add_clause([-d, -x, -y])
            solver.add_clause([d, -x, y])
            solver.add_clause([d, x, -y])

        solver.add_clause(diffs)

        for aidx, dfa in enumerate(dfas[:level]):
            add_dfa_constraint(
                solver,
                pool,
                dfa,
                aidx,
                xvars,
                yvars,
            )

        build_time = time.perf_counter() - build_start

        solve_start = time.perf_counter()
        sat = solver.solve()
        solve_time = time.perf_counter() - solve_start

        print()
        print("=" * 60)
        print(f"DFA constraints = {level}")
        print(f"variables       = {pool.top}")
        print(f"build time      = {build_time:.3f}s")
        print(f"solve time      = {solve_time:.3f}s")
        print(f"status          = {'SAT' if sat else 'UNSAT'}")

        if sat:
            model_set = set(
                lit for lit in solver.get_model()
                if lit > 0
            )

            u = decode_word(model_set, xvars)
            v = decode_word(model_set, yvars)

            print("u =", u)
            print("v =", v)
            print("different =", u != v)

        return sat, solve_time


def main():
    print("===== V5.4 BOOLEAN SAT BENCHMARK =====")
    print("word length =", N)
    print("levels =", LEVELS)

    max_level = max(LEVELS)

    start = time.perf_counter()
    dfas = load_5_state_dfas(max_level)

    print(
        f"loaded {len(dfas)} 5-state DFAs "
        f"in {time.perf_counter() - start:.3f}s"
    )

    results = []

    for level in LEVELS:
        sat, solve_time = run_level(dfas, level)

        results.append((level, sat, solve_time))

        # Hard experimental stop:
        # don't continue scaling an obviously poor encoding.
        if solve_time > 120:
            print()
            print(
                "STOP: solve exceeded 120 seconds. "
                "Do not scale further."
            )
            break

    print()
    print("===== SUMMARY =====")

    for level, sat, sec in results:
        print(
            f"{level:>4} DFAs | "
            f"{'SAT' if sat else 'UNSAT':>5} | "
            f"{sec:>10.3f}s"
        )


if __name__ == "__main__":
    main()
