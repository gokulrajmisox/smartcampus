"""Reproducible benchmark for smartcampus (CampusAI) pathfinding algorithms.

Measures every algorithm the repo ships (BFS, DFS, UCS, A* Euclidean,
A* Manhattan, A* Combined) on the repo's own campus graph
(attached_assets/sathyabama_small.osm) over every ordered pair of the
12 POIs in campus_data/demo_locations.json.

UCS is the ground truth for weighted shortest path, so each algorithm's
optimality gap is reported against UCS on the same route.

What is measured (and what is NOT):
  - The search methods themselves (bfs_osm / dfs_osm / ucs_osm /
    astar_*). find_path() is deliberately NOT used: it builds a Folium
    map on every call, which would swamp the search timings.
  - BFS/DFS report distance via calculate_path_distance(), exactly as
    find_path() does; UCS/A* report their accumulated cost. (Known
    inconsistency, Day 15 finding: missing edge `length` defaults to
    1.0 in UCS/A* accumulation but 0.0 in calculate_path_distance.)
  - Timing is the median of N repetitions (default 5) per route per
    algorithm, measured with time.perf_counter() around the search
    call only. Graph load time is reported separately, once.

Run from the repository root (the pathfinder reads
campus_data/demo_locations.json relative to the working directory):

    python benchmarks/pathfinding_benchmark.py [--repetitions 5] \
        [--output benchmarks/pathfinding_results.json]

Requires the repo's runtime deps (osmnx, networkx, folium). No
dataset, network access, or API keys are needed.
"""

import argparse
import hashlib
import itertools
import json
import logging
import statistics
import sys
import time
from pathlib import Path

import osmnx as ox

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pathfinding import CampusPathfinder  # noqa: E402

ALGORITHMS = {
    "BFS": "bfs_osm",
    "DFS": "dfs_osm",
    "UCS": "ucs_osm",
    "A* (Euclidean)": "astar_euclidean",
    "A* (Manhattan)": "astar_manhattan",
    "A* (Combined)": "astar_combined",
}


def run_search(pf, method_name, start_node, end_node):
    """Run one search; return (distance_m, nodes_explored, path_len)."""
    method = getattr(pf, method_name)
    result = method(start_node, end_node)
    if method_name in ("bfs_osm", "dfs_osm"):
        path, explored = result
        distance = pf.calculate_path_distance(path) if path else None
    else:
        path, distance, explored = result
    if path is None:
        return None, len(explored), 0
    return distance, len(explored), len(path)


def median_time_ms(pf, method_name, start_node, end_node, repetitions):
    """Median wall time in ms over `repetitions` runs (last run's metrics kept)."""
    times = []
    metrics = None
    for _ in range(repetitions):
        t0 = time.perf_counter()
        metrics = run_search(pf, method_name, start_node, end_node)
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times), metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--osm", default="attached_assets/sathyabama_small.osm")
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--output", default="benchmarks/pathfinding_results.json")
    args = parser.parse_args()

    # Silence the repo's JSON logger during timing; it would otherwise
    # print one line per find_path-equivalent call (not per search, but
    # construction still logs). Search methods themselves do not log.
    logging.getLogger("campus_navigator").setLevel(logging.WARNING)

    t0 = time.perf_counter()
    pf = CampusPathfinder(args.osm)
    load_s = time.perf_counter() - t0

    poi_names = sorted(pf.POIS)
    nodes = {
        name: ox.distance.nearest_nodes(pf.graph, pf.POIS[name][1], pf.POIS[name][0])
        for name in poi_names
    }

    results = []
    for start_name, end_name in itertools.permutations(poi_names, 2):
        row = {"route": f"{start_name} -> {end_name}"}
        ucs_distance = None
        for algo, method_name in ALGORITHMS.items():
            ms, (distance, explored, path_len) = median_time_ms(
                pf, method_name, nodes[start_name], nodes[end_name], args.repetitions
            )
            row[algo] = {
                "found": distance is not None,
                "distance_m": distance,
                "nodes_explored": explored,
                "path_nodes": path_len,
                "median_ms": round(ms, 3),
            }
            if algo == "UCS":
                ucs_distance = distance
        # Optimality gap vs UCS on this route (None when either side failed).
        for algo in ALGORITHMS:
            entry = row[algo]
            if entry["found"] and ucs_distance:
                entry["gap_vs_ucs_pct"] = round(
                    (entry["distance_m"] - ucs_distance) / ucs_distance * 100.0, 4
                )
            else:
                entry["gap_vs_ucs_pct"] = None
        results.append(row)

    pathfinding_py = Path("src/pathfinding.py")
    report = {
        "repo": "gokulrajmisox/smartcampus",
        "code": {
            "src/pathfinding.py sha256": hashlib.sha256(
                pathfinding_py.read_bytes()
            ).hexdigest(),
        },
        "graph": {
            "osm_file": args.osm,
            "nodes": pf.graph.number_of_nodes(),
            "edges": pf.graph.number_of_edges(),
            "pois": len(poi_names),
            "load_seconds": round(load_s, 3),
        },
        "method": {
            "routes": "all ordered POI pairs (12 x 11 = 132)",
            "repetitions_per_route_per_algorithm": args.repetitions,
            "timing": "median of repetitions, perf_counter around the search call only",
            "ground_truth": "UCS distance on the same route",
            "excluded_from_search_timing": "find_path() Folium map construction",
        },
        "environment": {
            "python": sys.version.split()[0],
            "osmnx": ox.__version__,
            "networkx": __import__("networkx").__version__,
        },
        "results": results,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Aggregate summary printed for the report.
    print(f"graph: {report['graph']['nodes']} nodes, "
          f"{report['graph']['edges']} edges, {len(poi_names)} POIs, "
          f"load {load_s:.2f}s")
    print(f"routes: {len(results)} ordered pairs x {len(ALGORITHMS)} algorithms "
          f"x {args.repetitions} reps")
    for algo in ALGORITHMS:
        entries = [r[algo] for r in results]
        found = [e for e in entries if e["found"]]
        gaps = [e["gap_vs_ucs_pct"] for e in found if e["gap_vs_ucs_pct"] is not None]
        subopt = [g for g in gaps if g > 0.01]
        print(f"{algo}: found {len(found)}/{len(entries)}, "
              f"mean_time_ms {statistics.mean(e['median_ms'] for e in found):.3f}, "
              f"mean_explored {statistics.mean(e['nodes_explored'] for e in found):.1f}, "
              f"mean_gap_pct {statistics.mean(gaps) if gaps else 0:.4f}, "
              f"max_gap_pct {max(gaps) if gaps else 0:.4f}, "
              f"suboptimal_routes {len(subopt)}")
    print(f"results written to {out}")


if __name__ == "__main__":
    main()
