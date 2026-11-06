# CampusAI pathfinding benchmark — first reproducible evaluation report

Repo: `gokulrajmisox/smartcampus` (CampusAI). Code measured: `src/pathfinding.py`
on main, SHA-256 `1b7a968465a63e2c…` (full hash in the JSON run output;
the file was byte-identical to the copy inspected on Day 16, so main's
pathfinding module is unchanged since then).

## What was measured

All six algorithms the repo ships — BFS, DFS, UCS, A\* (Euclidean),
A\* (Manhattan), A\* (Combined) — over **every ordered pair of the 12
POIs** in `campus_data/demo_locations.json` (12 × 11 = **132 routes**)
on the repo's own campus graph, `attached_assets/sathyabama_small.osm`
(**1,059 nodes, 1,920 edges**).

UCS is the ground truth for weighted shortest path, so each algorithm's
**optimality gap** is its distance minus the UCS distance on the same
route, as a percentage. The search methods themselves were timed
(`bfs_osm` / `dfs_osm` / `ucs_osm` / `astar_*`); `find_path()` was
deliberately not used because it builds a Folium map on every call,
which would swamp the search timings. Each timing is the median of
5 repetitions per route per algorithm (`time.perf_counter()` around
the search call only).

## Results

| Algorithm | Routes found | Mean time / route | Mean nodes explored | Mean gap vs UCS | Max gap vs UCS | Routes suboptimal (>0.01%) |
|---|---|---|---|---|---|---|
| BFS | 132/132 | 0.27 ms | 311.8 | +8.73% | +77.39% | 95 |
| DFS | 132/132 | 0.56 ms | 461.1 | +227.81% | +2385.38% | 124 |
| UCS (ground truth) | 132/132 | 0.75 ms | 326.9 | 0% | 0% | 0 |
| A\* (Euclidean) | 132/132 | 0.67 ms | 173.8 | +0.016% | +1.47% | 10 |
| A\* (Manhattan) | 132/132 | 0.51 ms | 143.9 | +0.234% | +3.40% | 48 |
| A\* (Combined) | 132/132 | 0.83 ms | 162.5 | +0.035% | +1.47% | 18 |

Every algorithm finds a route for every ordered POI pair on this
directed graph. Graph load takes ~0.11 s and is excluded from the
per-route timings.

## What the numbers mean

- **The Day 15 inadmissibility finding is now confirmed on real campus
  routes, not just a synthetic graph.** A\* (Manhattan) returns a
  longer-than-shortest route on 48 of 132 real routes (worst:
  Accessible Washroom → Block B, 367.8 m vs the true 355.7 m, +3.40%;
  next worst: Hostel → Accessible Washroom +2.15%, Block B → Main
  Gate +1.76%). A\* (Combined) inherits the same defect on 18 routes.
  A\* (Euclidean) is near-optimal but not exact either — 10 routes
  suboptimal, worst Block B → CSE Laboratory +1.47% — consistent with
  the flat 111,000 m/degree factor overestimating east–west distance
  by ~2.4% at this latitude. Until the heuristic is fixed, only UCS
  (and, on most routes, A\* Euclidean) should be presented as
  "shortest".
- **BFS and DFS are not shortest-path algorithms, and the gap is
  large.** BFS averages +8.7% over UCS and is suboptimal on 95/132
  routes; DFS averages +227.8% and is suboptimal on 124/132 (worst:
  Hostel → Medical Center, +2385%). Any UI copy or demo that presents
  a BFS/DFS route as "the route" without qualification overstates it.
- **Efficiency ranking is the reverse of the optimality ranking.**
  A\* (Manhattan) explores the fewest nodes on average (143.9 vs
  326.9 for UCS) — but that speed is bought with the suboptimality
  above. A\* (Euclidean) is the best trade-off on this graph: roughly
  half UCS's node expansions (173.8) with a mean gap of only 0.016%.
- **Absolute timings are small and should not be over-read.** This is
  a 1,059-node campus graph; every algorithm averages under 1 ms per
  route, so the mean-time column mostly reflects Python overhead, not
  algorithmic scaling. Node-expansion counts are the more stable
  efficiency signal here. A larger graph would be needed to benchmark
  scaling (e.g. the BFS/DFS visited-on-pop frontier blowup noted on
  Day 15).

## Environment (this run, 2026-11-05)

Python 3.12.3, osmnx 2.1.1, networkx 3.7, folium (repo dependency).
Single run on one VM; a repeat run reproduced every distance and
node-expansion count exactly — only the sub-millisecond timings moved.
No network access, dataset, or API key is needed to reproduce.

## How to reproduce

From the repository root:

```bash
python benchmarks/pathfinding_benchmark.py [--repetitions 5] \
    [--output benchmarks/pathfinding_results.json]
```

The script prints the aggregate table and writes per-route JSON
(distances, nodes explored, path lengths, median times, gaps vs UCS)
to the `--output` path. It requires the repo layout intact
(`src/`, `campus_data/demo_locations.json`,
`attached_assets/sathyabama_small.osm`) because the pathfinder reads
the POI file relative to the working directory.

## Limitations (honest scope)

- BFS/DFS distances use `calculate_path_distance()`, exactly as
  `find_path()` does, while UCS/A\* report accumulated cost. Missing
  edge `length` defaults to 1.0 in UCS/A\* but 0.0 in
  `calculate_path_distance()` (Day 15 finding), so a small part of
  the BFS/DFS gap on routes with length-less edges is a metric
  inconsistency, not search quality.
- Accessibility mode was not benchmarked (it routes through the
  key-0-only `is_edge_accessible` check pinned by the Day 16
  tripwires).
- One graph, one machine, one POI set. Results describe this campus
  graph; they do not generalize to city-scale graphs.
