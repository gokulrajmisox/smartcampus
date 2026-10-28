"""Optimality + accessibility regression tests for CampusPathfinder (Day 16).

Pins two Day 15 findings BEFORE any fix, so the fix day can flip them green:

1. A* Manhattan / Combined heuristics are inadmissible: on a graph whose
   edge lengths are all >= straight-line distance (a realistic road graph),
   they still return a suboptimal route, while UCS returns the true shortest
   path. UCS is the ground truth for weighted shortest path.
2. ``is_edge_accessible`` reads only parallel-edge key 0: if key 0 is a
   blocked highway (e.g. steps) but a parallel edge is accessible, the
   route is wrongly blocked in accessibility mode.

The ``xfail(strict=True)`` tests below are EXPECTED failures on current
main: they document the defects. When the fix lands, they become XPASS and
fail strictly, which is the intended tripwire -- update or unmark them then.

The tests build tiny synthetic MultiDiGraphs and attach them to a
CampusPathfinder instance WITHOUT running ``__init__`` (no OSM file, no
Folium map, no network access). The search methods under test touch only
``self.graph``, so this exercises the production code paths faithfully.
"""

import networkx as nx
import pytest

from src.pathfinding import CampusPathfinder


def _pathfinder_with_graph(graph):
    """Build a CampusPathfinder bound to a synthetic graph (no __init__)."""
    pathfinder = object.__new__(CampusPathfinder)
    pathfinder.graph = graph
    return pathfinder


def _optimality_graph():
    """Three-node graph with realistic (straight-line-consistent) lengths.

    Coordinates are degrees; the 111000 m/degree factor in the heuristics
    converts them to meters. Edge lengths are all >= straight-line distance:

    - S (0.0, 0.0) -> M (0.5, 0.5): length 80,000 m (straight line 78,489 m)
    - M (0.5, 0.5) -> G (1.0, 1.0): length 80,000 m (straight line 78,489 m)
    - S (0.0, 0.0) -> G (1.0, 1.0): length 165,000 m (straight line 156,978 m)

    True shortest path: S -> M -> G = 160,000 m. Direct S -> G = 165,000 m.
    """
    graph = nx.MultiDiGraph()
    graph.add_node(1, y=0.0, x=0.0)  # S
    graph.add_node(2, y=0.5, x=0.5)  # M
    graph.add_node(3, y=1.0, x=1.0)  # G
    graph.add_edge(1, 2, length=80_000.0)
    graph.add_edge(2, 3, length=80_000.0)
    graph.add_edge(1, 3, length=165_000.0)
    return graph


@pytest.fixture
def optimality_pathfinder():
    return _pathfinder_with_graph(_optimality_graph())


def test_ucs_is_ground_truth(optimality_pathfinder):
    """UCS returns the true shortest path S -> M -> G = 160,000 m."""
    path, cost, _ = optimality_pathfinder.ucs_osm(1, 3)

    assert path == [1, 2, 3]
    assert cost == pytest.approx(160_000.0)


def test_astar_euclidean_is_optimal(optimality_pathfinder):
    """A* Euclidean agrees with UCS on this consistent graph."""
    path, cost, _ = optimality_pathfinder.astar_euclidean(1, 3)

    assert path == [1, 2, 3]
    assert cost == pytest.approx(160_000.0)


@pytest.mark.xfail(
    strict=True,
    reason="Day 15: Manhattan heuristic is inadmissible -- it overestimates "
    "the true remaining cost (111,000 m vs 80,000 m from M), so A* pops "
    "the direct 165,000 m edge before the optimal 160,000 m route.",
)
def test_astar_manhattan_is_optimal(optimality_pathfinder):
    """A* Manhattan must agree with UCS -- currently returns 165,000 m."""
    path, cost, _ = optimality_pathfinder.astar_manhattan(1, 3)

    assert path == [1, 2, 3]
    assert cost == pytest.approx(160_000.0)


@pytest.mark.xfail(
    strict=True,
    reason="Day 15: Combined heuristic inherits the Manhattan overestimate "
    "(0.7 * Euclidean + 0.3 * Manhattan = 88,242 m vs true 80,000 m from "
    "M), so A* pops the direct 165,000 m edge before the optimal route.",
)
def test_astar_combined_is_optimal(optimality_pathfinder):
    """A* Combined must agree with UCS -- currently returns 165,000 m."""
    path, cost, _ = optimality_pathfinder.astar_combined(1, 3)

    assert path == [1, 2, 3]
    assert cost == pytest.approx(160_000.0)


def test_heuristic_overestimate_mechanism(optimality_pathfinder):
    """Documents WHY Manhattan/Combined fail: they overestimate M -> G.

    True remaining cost from M to G is 80,000 m. Manhattan estimates
    111,000 m and Combined 88,242 m (both overestimates); Euclidean
    estimates 78,489 m (admissible here). This test passes on current main
    and pins the mechanism, not the outcome.
    """
    manhattan = optimality_pathfinder.manhattan_heuristic(2, 3)
    combined = optimality_pathfinder.combined_heuristic(2, 3)
    euclidean = optimality_pathfinder.euclidean_heuristic(2, 3)

    assert manhattan == pytest.approx(111_000.0)
    assert manhattan > 80_000.0
    assert combined == pytest.approx(88_242.0, abs=1.0)
    assert combined > 80_000.0
    assert euclidean == pytest.approx(78_489.0, abs=1.0)
    assert euclidean <= 80_000.0


def _parallel_edge_graph(key0_highway, key1_highway):
    """Two nodes joined by two parallel edges (keys 0 and 1)."""
    graph = nx.MultiDiGraph()
    graph.add_node(10, y=0.0, x=0.0)
    graph.add_node(20, y=0.0, x=0.001)
    graph.add_edge(10, 20, key=0, highway=key0_highway, length=10.0)
    graph.add_edge(10, 20, key=1, highway=key1_highway, length=12.0)
    return graph


@pytest.mark.xfail(
    strict=True,
    reason="Day 15: is_edge_accessible reads only parallel-edge key 0, so "
    "an accessible parallel edge (key 1) is ignored and the edge is "
    "wrongly reported inaccessible.",
)
def test_is_edge_accessible_considers_parallel_edges():
    """An accessible parallel edge must make the edge accessible."""
    pathfinder = _pathfinder_with_graph(
        _parallel_edge_graph("steps", "footway")
    )

    assert pathfinder.is_edge_accessible(10, 20) is True


@pytest.mark.xfail(
    strict=True,
    reason="Day 15: accessibility-mode routing inherits the key-0-only "
    "check, so UCS finds no route even though a parallel edge is usable.",
)
def test_accessibility_route_uses_parallel_edge():
    """UCS in accessibility mode must route over the accessible edge."""
    pathfinder = _pathfinder_with_graph(
        _parallel_edge_graph("steps", "footway")
    )

    path, cost, _ = pathfinder.ucs_osm(10, 20, accessibility_mode=True)

    assert path == [10, 20]
    assert cost == pytest.approx(10.0)


def test_is_edge_accessible_all_blocked():
    """If every parallel edge is blocked, the edge stays inaccessible."""
    pathfinder = _pathfinder_with_graph(
        _parallel_edge_graph("steps", "stairs")
    )

    assert pathfinder.is_edge_accessible(10, 20) is False


def test_is_edge_accessible_key0_accessible():
    """A key-0 accessible edge is accessible (current behavior, kept)."""
    pathfinder = _pathfinder_with_graph(
        _parallel_edge_graph("footway", "steps")
    )

    assert pathfinder.is_edge_accessible(10, 20) is True


def test_accessibility_route_over_accessible_edge():
    """UCS in accessibility mode routes over a plain accessible edge."""
    graph = nx.MultiDiGraph()
    graph.add_node(10, y=0.0, x=0.0)
    graph.add_node(20, y=0.0, x=0.001)
    graph.add_edge(10, 20, highway="footway", length=12.0)
    pathfinder = _pathfinder_with_graph(graph)

    path, cost, _ = pathfinder.ucs_osm(10, 20, accessibility_mode=True)

    assert path == [10, 20]
    assert cost == pytest.approx(12.0)
