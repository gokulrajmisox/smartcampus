import pytest
from src.pathfinding import CampusPathfinder, PathNotFoundError

@pytest.fixture(scope="module")
def pathfinder():
    """Fixture to initialize CampusPathfinder with test OSM data."""
    return CampusPathfinder("attached_assets/map_1758707724808.osm")

def test_initialization(pathfinder):
    """Test standard parameters initialization."""
    assert pathfinder.graph is not None
    assert "Library" in pathfinder.POIS
    assert "Entry gate" in pathfinder.POIS
    assert pathfinder.WALKING_SPEED == 1.4

def test_heuristics(pathfinder):
    """Test heuristic calculators returning valid positive bounds."""
    # Find two nearby node IDs
    nodes = list(pathfinder.graph.nodes)
    n1, n2 = nodes[0], nodes[1]
    
    val_euclidean = pathfinder.euclidean_heuristic(n1, n2)
    val_manhattan = pathfinder.manhattan_heuristic(n1, n2)
    val_combined = pathfinder.combined_heuristic(n1, n2)
    
    assert val_euclidean >= 0.0
    assert val_manhattan >= 0.0
    assert val_combined >= 0.0

def test_pathfinding_algorithms(pathfinder):
    """Test all search strategies return valid path vectors and explored logs."""
    start_poi = "Entry gate"
    end_poi = "Library"
    
    for algo in ["BFS", "DFS", "UCS", "A* (Euclidean)", "A* (Manhattan)", "A* (Combined)"]:
        result = pathfinder.find_path(start_poi, end_poi, algo)
        assert result is not None
        assert 'map' in result
        assert 'metrics' in result
        metrics = result['metrics']
        assert metrics['distance'] > 0.0
        assert metrics['time'] > 0.0
        assert metrics['nodes_explored'] > 0
        assert metrics['start_location'] == start_poi
        assert metrics['end_location'] == end_poi

def test_pathfinding_invalid_pois(pathfinder):
    """Test invalid POI names raise KeyError."""
    with pytest.raises(KeyError):
        pathfinder.find_path("NonExistentStart", "Library", "A*")
        
    with pytest.raises(KeyError):
        pathfinder.find_path("Library", "NonExistentEnd", "A*")
        
def test_path_distance_calculation(pathfinder):
    """Test total distance calculation returns expected non-negative values."""
    start_poi = "Entry gate"
    end_poi = "Library"
    
    # Run UCS to get a path
    result = pathfinder.find_path(start_poi, end_poi, "UCS")
    # Retrieve the nodes explored or final nodes
    # Let's extract start & end node
    start_latlon = pathfinder.POIS[start_poi]
    end_latlon = pathfinder.POIS[end_poi]
    import osmnx as ox
    start_node = ox.distance.nearest_nodes(pathfinder.graph, start_latlon[1], start_latlon[0])
    end_node = ox.distance.nearest_nodes(pathfinder.graph, end_latlon[1], end_latlon[0])
    
    path, cost, _ = pathfinder.ucs_osm(start_node, end_node)
    
    assert path is not None
    calculated_dist = pathfinder.calculate_path_distance(path)
    assert calculated_dist == cost
