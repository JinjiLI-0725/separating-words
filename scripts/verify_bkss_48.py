from separating_words.canonical_generator import generate_canonical_dfas
from separating_words.dfa import DFA

k = 5
L = 12

u = "01" * (k - 2 + L) + "10" * k + "01" * (k - 1)
v = "01" * (k - 2)     + "10" * k + "01" * (k - 1 + L)

assert len(u) == 48
assert len(v) == 48
assert u != v

print("===== BKSS LENGTH-48 VERIFICATION =====")
print("u =", u)
print("v =", v)
print("length =", len(u))

total = 0
separators = 0

for states in range(1, 6):
    count = 0
    sep_count = 0

    for transitions in generate_canonical_dfas(states):
        count += 1
        dfa = DFA(transitions)

        if dfa.run(u) != dfa.run(v):
            sep_count += 1

    total += count
    separators += sep_count

    print(
        f"k={states}: automata={count:,} "
        f"separators={sep_count:,}"
    )

print()
print("total automata =", f"{total:,}")
print("total separators =", separators)

if total != 166_152:
    raise RuntimeError(f"Unexpected DFA count: {total}")

if separators != 0:
    raise RuntimeError("BKSS pair was separated!")

print()
print("VERIFIED: no <=5-state canonical DFA separates the BKSS pair.")
print("Therefore sep(u,v) >= 6.")
