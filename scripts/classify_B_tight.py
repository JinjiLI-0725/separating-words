#!/usr/bin/env python3

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

from triangle_free.research import from_graph6

TSV = Path("results/induction_B_tight_existing.tsv")
EVAL = Path("results/heuristic_k3/evaluations.jsonl")

sources = defaultdict(set)

for line in EVAL.read_text().splitlines():
    row = json.loads(line)
    sources[row["graph6"]].add(row["source"])

rows = []

with TSV.open() as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        g6 = row["graph6"]
        G = from_graph6(g6)

        adj = G.adjacency_masks()
        degrees = tuple(
            sorted((adj[v].bit_count() for v in range(G.n)),
                   reverse=True)
        )

        rows.append({
            "graph6": g6,
            "d": int(row["d"]),
            "m": int(row["m"]),
            "M": int(row["M"]),
            "balanced": bool(int(row["balanced"])),
            "core_mask": int(row["core_mask"]),
            "degree_sequence": degrees,
            "sources": sorted(sources[g6]),
            "graph": G,
        })

print("tight labeled graphs =", len(rows))

print("\n=== d distribution ===")
print(Counter(r["d"] for r in rows))

print("\n=== balanced distribution ===")
print(Counter(r["balanced"] for r in rows))

print("\n=== (d,m,balanced) distribution ===")
for key, count in sorted(
    Counter((r["d"], r["m"], r["balanced"]) for r in rows).items()
):
    print(key, count)

print("\n=== source-family distribution ===")
family_counter = Counter()

for r in rows:
    for family in {s.split(":",1)[0] for s in r["sources"]}:
        family_counter[family] += 1

for family, count in family_counter.most_common():
    print(f"{family}: {count}")

def to_nx(G):
    H = nx.Graph()
    H.add_nodes_from(range(G.n))
    H.add_edges_from(G.edges)
    return H

classes = []

for r in rows:
    H = to_nx(r["graph"])
    found = False

    for cls in classes:
        if nx.is_isomorphic(H, cls["representative_nx"]):
            cls["members"].append(r)
            found = True
            break

    if not found:
        classes.append({
            "representative": r,
            "representative_nx": H,
            "members": [r],
        })

classes.sort(
    key=lambda c: (
        c["representative"]["balanced"],
        c["representative"]["d"],
        c["representative"]["m"],
        -len(c["members"]),
    )
)

print("\n=== ISOMORPHISM CLASSES ===")
print("number of classes =", len(classes))

for i, cls in enumerate(classes, 1):
    r = cls["representative"]

    fams = sorted({
        src.split(":",1)[0]
        for member in cls["members"]
        for src in member["sources"]
    })

    print(
        f"\nclass {i}:"
        f" labeled={len(cls['members'])}"
        f" d={r['d']}"
        f" m={r['m']}"
        f" M={r['M']}"
        f" balanced={r['balanced']}"
    )
    print("degree_sequence =", r["degree_sequence"])
    print("representative =", r["graph6"])
    print("families =", fams)

out = {
    "tight_labeled_graphs": len(rows),
    "isomorphism_classes": len(classes),
    "d_distribution": dict(sorted(Counter(r["d"] for r in rows).items())),
    "classes": [],
}

for i, cls in enumerate(classes, 1):
    r = cls["representative"]

    out["classes"].append({
        "class": i,
        "labeled_count": len(cls["members"]),
        "representative_graph6": r["graph6"],
        "d": r["d"],
        "m": r["m"],
        "M": r["M"],
        "balanced": r["balanced"],
        "degree_sequence": list(r["degree_sequence"]),
        "families": sorted({
            src.split(":",1)[0]
            for member in cls["members"]
            for src in member["sources"]
        }),
    })

Path("results/induction_B_tight_classification.json").write_text(
    json.dumps(out, indent=2) + "\n"
)
