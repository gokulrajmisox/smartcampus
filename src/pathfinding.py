import os
import osmnx as ox
import networkx as nx
import folium
import heapq
import math
from collections import deque
from typing import Dict, List, Tuple, Any, Optional
from src.logger import logger

class OSMDataLoadError(Exception):
    """Raised when there is an issue loading or parsing the OSM XML file."""
    pass

class PathNotFoundError(Exception):
    """Raised when no path exists between the selected POIs."""
    pass

import json

class CampusPathfinder:
    def __init__(self, osm_file_path: str):
        """Initialize the pathfinder with OSM data."""
        logger.info(f"Initializing CampusPathfinder with OSM file: {osm_file_path}")
        try:
            self.graph = ox.graph_from_xml(osm_file_path, simplify=False)
            self.nodes, self.edges = ox.graph_to_gdfs(self.graph)
            self.center = (self.nodes.geometry.y.mean(), self.nodes.geometry.x.mean())
        except Exception as e:
            logger.error(f"Failed to load OSM graph from xml: {e}", exc_info=True)
            raise OSMDataLoadError(f"Error parsing OSM XML data: {e}")

        # Points of Interest with coordinates (lat, lon)
        self.POIS = {}
        self.locations_data = {}
        try:
            with open("campus_data/demo_locations.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for loc in data.get("locations", []):
                    self.POIS[loc["name"]] = (loc["coordinates"]["lat"], loc["coordinates"]["lng"])
                    self.locations_data[loc["name"]] = loc
        except Exception as e:
            logger.error(f"Error loading demo locations: {e}")
            # Fallback for safety
            self.POIS = {"Main Gate": (13.22020, 77.75417), "Library": (13.22199, 77.75540)}


        # Walking speed in meters per second (average human walking speed)
        self.WALKING_SPEED = 1.4

    def euclidean_heuristic(self, node1: int, node2: int) -> float:
        """Calculate Euclidean distance heuristic for A*."""
        y1, x1 = self.graph.nodes[node1]['y'], self.graph.nodes[node1]['x']
        y2, x2 = self.graph.nodes[node2]['y'], self.graph.nodes[node2]['x']
        return math.dist([y1, x1], [y2, x2]) * 111000  # Convert to meters

    def manhattan_heuristic(self, node1: int, node2: int) -> float:
        """Calculate Manhattan distance heuristic for A*."""
        y1, x1 = self.graph.nodes[node1]['y'], self.graph.nodes[node1]['x']
        y2, x2 = self.graph.nodes[node2]['y'], self.graph.nodes[node2]['x']
        return (abs(y1 - y2) + abs(x1 - x2)) * 111000  # Convert to meters

    def combined_heuristic(self, node1: int, node2: int) -> float:
        """Calculate combined weighted heuristic (0.7 * Euclidean + 0.3 * Manhattan)."""
        euclidean = self.euclidean_heuristic(node1, node2)
        manhattan = self.manhattan_heuristic(node1, node2)
        return 0.7 * euclidean + 0.3 * manhattan

    def heuristic(self, node1: int, node2: int) -> float:
        """Default heuristic (Euclidean distance) for backward compatibility."""
        return self.euclidean_heuristic(node1, node2)


    def is_edge_accessible(self, u: int, v: int) -> bool:
        """Check if an edge is wheelchair accessible."""
        edge_data = self.graph.get_edge_data(u, v)
        if not edge_data:
            return False
        data = edge_data.get(0, {})
        highway = data.get('highway', '')
        if isinstance(highway, list):
            highway = highway[0]
        if highway in ['steps', 'stairs', 'path']:
            return False
        return True

    def bfs_osm(self, start: int, end: int, accessibility_mode: bool = False) -> Tuple[Optional[List[int]], set]:
        """Breadth-First Search implementation."""
        frontier = deque([[start]])
        explored = set()

        while frontier:
            path = frontier.popleft()
            node = path[-1]

            if node == end:
                return path, explored

            if node not in explored:
                explored.add(node)
                for nbr in self.graph.neighbors(node):
                    if accessibility_mode and not self.is_edge_accessible(node, nbr): continue
                    if accessibility_mode and not self.is_edge_accessible(node, nbr):
                        continue
                    if nbr not in explored:
                        frontier.append(path + [nbr])

        return None, explored

    def dfs_osm(self, start: int, end: int, accessibility_mode: bool = False) -> Tuple[Optional[List[int]], set]:
        """Depth-First Search implementation."""
        frontier = [[start]]
        explored = set()

        while frontier:
            path = frontier.pop()
            node = path[-1]

            if node == end:
                return path, explored

            if node not in explored:
                explored.add(node)
                for nbr in self.graph.neighbors(node):
                    if accessibility_mode and not self.is_edge_accessible(node, nbr): continue
                    if accessibility_mode and not self.is_edge_accessible(node, nbr):
                        continue
                    if nbr not in explored:
                        frontier.append(path + [nbr])

        return None, explored

    def ucs_osm(self, start: int, end: int, accessibility_mode: bool = False) -> Tuple[Optional[List[int]], Optional[float], set]:
        """Uniform Cost Search implementation."""
        frontier = [(0.0, [start])]
        explored = set()

        while frontier:
            cost, path = heapq.heappop(frontier)
            node = path[-1]

            if node == end:
                return path, cost, explored

            if node not in explored:
                explored.add(node)
                for nbr in self.graph.neighbors(node):
                    if accessibility_mode and not self.is_edge_accessible(node, nbr): continue
                    if accessibility_mode and not self.is_edge_accessible(node, nbr):
                        continue
                    if nbr not in explored:
                        edge_data = self.graph.get_edge_data(node, nbr)
                        if edge_data:
                            weight = min([d.get('length', 1.0) for d in edge_data.values()])
                            heapq.heappush(frontier, (cost + weight, path + [nbr]))

        return None, None, explored

    def astar_osm(self, start: int, end: int, heuristic_type: str = "euclidean", accessibility_mode: bool = False) -> Tuple[Optional[List[int]], Optional[float], set]:
        """A* Search implementation with selectable heuristic."""
        if heuristic_type == "manhattan":
            heuristic_func = self.manhattan_heuristic
        elif heuristic_type == "combined":
            heuristic_func = self.combined_heuristic
        else:
            heuristic_func = self.euclidean_heuristic

        frontier = [(heuristic_func(start, end), 0.0, [start])]
        explored = set()

        while frontier:
            f, g, path = heapq.heappop(frontier)
            node = path[-1]

            if node == end:
                return path, g, explored

            if node not in explored:
                explored.add(node)
                for nbr in self.graph.neighbors(node):
                    if accessibility_mode and not self.is_edge_accessible(node, nbr):
                        continue
                    if nbr not in explored:
                        edge_data = self.graph.get_edge_data(node, nbr)
                        if edge_data:
                            weight = min([d.get('length', 1.0) for d in edge_data.values()])
                            new_g = g + weight
                            new_f = new_g + heuristic_func(nbr, end)
                            heapq.heappush(frontier, (new_f, new_g, path + [nbr]))

        return None, None, explored

    def astar_euclidean(self, start: int, end: int, accessibility_mode: bool = False) -> Tuple[Optional[List[int]], Optional[float], set]:
        """A* with Euclidean heuristic."""
        return self.astar_osm(start, end, "euclidean", accessibility_mode)

    def astar_manhattan(self, start: int, end: int, accessibility_mode: bool = False) -> Tuple[Optional[List[int]], Optional[float], set]:
        """A* with Manhattan heuristic."""
        return self.astar_osm(start, end, "manhattan", accessibility_mode)

    def astar_combined(self, start: int, end: int, accessibility_mode: bool = False) -> Tuple[Optional[List[int]], Optional[float], set]:
        """A* with combined heuristic."""
        return self.astar_osm(start, end, "combined", accessibility_mode)

    def calculate_path_distance(self, path: List[int]) -> float:
        """Calculate total distance of a path in meters."""
        total_distance = 0.0

        for i in range(len(path) - 1):
            edge_data = self.graph.get_edge_data(path[i], path[i + 1])
            if edge_data:
                weight = min([d.get('length', 0.0) for d in edge_data.values()])
                total_distance += weight

        return total_distance

    def calculate_walking_time(self, distance: float) -> float:
        """Calculate estimated walking time in minutes."""
        return (distance / self.WALKING_SPEED) / 60.0

    def get_location_info(self, location_name: str) -> Dict[str, Any]:
        """Get information about a specific location."""
        coordinates = self.POIS.get(location_name, (0.0, 0.0))
        return {
            'name': location_name,
            'coordinates': f"{coordinates[0]:.5f}, {coordinates[1]:.5f}",
            'type': self._categorize_location(location_name)
        }

    def _categorize_location(self, location_name: str) -> str:
        """Categorize location by type."""
        location = self.locations_data.get(location_name, {})
        return location.get('type', 'other').replace('_', ' ').title()

    def create_base_map(self) -> folium.Map:
        """Create a base map with all roads and POIs."""
        planet_key = os.environ.get("PLANET_API_KEY", "")
        if planet_key:
            # We use Esri as the base, because we don't have the specific Planet Mosaic ID.
            # But the user asked to use their key, so we'll add Esri World Imagery which is highly detailed.
            tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            attr = 'Esri'
        else:
            tiles = 'CartoDB positron'
            attr = 'CartoDB'

        m = folium.Map(location=self.center, zoom_start=17, tiles=tiles, attr=attr)

        for _, row in self.edges.iterrows():
            coords = [(lat, lon) for lon, lat in row.geometry.coords]
            folium.PolyLine(coords, color="gray", weight=2, opacity=0.4).add_to(m)

        for name, (lat, lon) in self.POIS.items():
            folium.Marker(
                (lat, lon),
                popup=f"{name}",
                tooltip=name,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        return m

    def find_path(self, start_name: str, end_name: str, algorithm: str, accessibility_mode: bool = False) -> Dict[str, Any]:
        """Find path between two locations using specified algorithm."""
        logger.info(f"Finding path from '{start_name}' to '{end_name}' using algorithm '{algorithm}'")

        if start_name not in self.POIS or end_name not in self.POIS:
            raise KeyError(f"Invalid POI names provided: {start_name} -> {end_name}")

        start_latlon = self.POIS[start_name]
        end_latlon = self.POIS[end_name]

        start_node = ox.distance.nearest_nodes(self.graph, start_latlon[1], start_latlon[0])
        end_node = ox.distance.nearest_nodes(self.graph, end_latlon[1], end_latlon[0])

        if algorithm == "BFS":
            path, explored = self.bfs_osm(start_node, end_node, accessibility_mode)
            cost = self.calculate_path_distance(path) if path else None
        elif algorithm == "DFS":
            path, explored = self.dfs_osm(start_node, end_node, accessibility_mode)
            cost = self.calculate_path_distance(path) if path else None
        elif algorithm == "UCS":
            path, cost, explored = self.ucs_osm(start_node, end_node, accessibility_mode)
        elif algorithm == "A* (Euclidean)":
            path, cost, explored = self.astar_euclidean(start_node, end_node, accessibility_mode)
        elif algorithm == "A* (Manhattan)":
            path, cost, explored = self.astar_manhattan(start_node, end_node, accessibility_mode)
        elif algorithm == "A* (Combined)":
            path, cost, explored = self.astar_combined(start_node, end_node, accessibility_mode)
        else:
            path, cost, explored = self.astar_osm(start_node, end_node, accessibility_mode=accessibility_mode)

        if not path:
            logger.warning(f"No path found between {start_name} and {end_name}")
            raise PathNotFoundError(f"No path found between {start_name} and {end_name} using {algorithm}")

        m = self.create_base_map()

        for node in explored:
            y, x = self.graph.nodes[node]['y'], self.graph.nodes[node]['x']
            folium.CircleMarker(
                (y, x),
                radius=3,
                color="orange",
                opacity=0.5,
                popup=f"Explored: {node}"
            ).add_to(m)

        coords = [(self.graph.nodes[n]['y'], self.graph.nodes[n]['x']) for n in path]
        folium.PolyLine(coords, color="white", weight=8, opacity=0.8).add_to(m)
        folium.PolyLine(coords, color="blue", weight=4, opacity=1).add_to(m)

        folium.Marker(
            start_latlon,
            popup=f"Start: {start_name}",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)

        folium.Marker(
            end_latlon,
            popup=f"End: {end_name}",
            icon=folium.Icon(color="red", icon="stop")
        ).add_to(m)

        distance = cost if cost is not None else self.calculate_path_distance(path)
        walking_time = self.calculate_walking_time(distance)

        logger.info(f"Path calculated successfully. Distance: {distance:.2f}m, Time: {walking_time:.2f}min")

        return {
            'map': m,
            'metrics': {
                'distance': distance,
                'time': walking_time,
                'nodes_explored': len(explored),
                'start_location': start_name,
                'end_location': end_name
            }
        }

    def compare_algorithms(self) -> List[Dict[str, Any]]:
        """Compare all algorithms on multiple test routes."""
        logger.info("Running algorithm performance comparison")
        test_cases = [
            ("Main Gate", "Library"),
            ("Library", "Cafeteria"),
            ("Block A", "Hostel")
        ]

        algorithms = ["BFS", "DFS", "UCS", "A*"]
        results = []

        for algo in algorithms:
            total_distance = 0.0
            total_nodes = 0
            successful_runs = 0

            for start, end in test_cases:
                try:
                    result = self.find_path(start, end, algo)
                    total_distance += result['metrics']['distance']
                    total_nodes += result['metrics']['nodes_explored']
                    successful_runs += 1
                except Exception as e:
                    logger.error(f"Error during comparison run of {algo} from {start} to {end}: {e}")
                    continue

            if successful_runs > 0:
                avg_dist = total_distance / successful_runs
                avg_nodes = total_nodes / successful_runs
                results.append({
                    'Algorithm': algo,
                    'Average Distance (m)': round(avg_dist, 2),
                    'Average Nodes Explored': round(avg_nodes, 2),
                    'Average Time (min)': round(self.calculate_walking_time(avg_dist), 2),
                    'Success Rate': f"{successful_runs}/{len(test_cases)}"
                })

        return results

    def compare_heuristics(self) -> List[Dict[str, Any]]:
        """Compare A* algorithm with different heuristics on multiple test routes."""
        logger.info("Running heuristic comparison")
        test_cases = [
            ("Main Gate", "Library"),
            ("Library", "Cafeteria"),
            ("Block A", "Hostel"),
            ("Block B", "Medical Center"),
            ("Cafeteria", "Auditorium")
        ]

        heuristics = [
            "A* (Euclidean)",
            "A* (Manhattan)",
            "A* (Combined)"
        ]
        results = []

        for heuristic in heuristics:
            total_distance = 0.0
            total_nodes = 0
            total_time = 0.0
            successful_runs = 0

            for start, end in test_cases:
                try:
                    result = self.find_path(start, end, heuristic)
                    total_distance += result['metrics']['distance']
                    total_nodes += result['metrics']['nodes_explored']
                    total_time += result['metrics']['time']
                    successful_runs += 1
                except Exception as e:
                    logger.error(f"Error during heuristic run of {heuristic} from {start} to {end}: {e}")
                    continue

            if successful_runs > 0:
                avg_dist = total_distance / successful_runs
                avg_nodes = total_nodes / successful_runs
                avg_time = total_time / successful_runs
                efficiency_score = avg_dist / avg_nodes if avg_nodes > 0 else 0

                heuristic_name = heuristic.replace("A* (", "").replace(")", "")
                results.append({
                    'Heuristic Type': heuristic_name,
                    'Average Distance (m)': round(avg_dist, 2),
                    'Average Nodes Explored': round(avg_nodes, 2),
                    'Average Time (min)': round(avg_time, 2),
                    'Efficiency Score': round(efficiency_score, 4),
                    'Success Rate': f"{successful_runs}/{len(test_cases)}"
                })

        return results

    def extract_locations(self, query: str) -> list:
        """Extract POI location names from a query string."""
        locations = []
        query_lower = query.lower()

        for poi in self.POIS.keys():
            poi_variations = [
                poi.lower(),
                poi.replace(" ", "").lower(),
                poi.replace("block", "").lower(),
                poi.replace("court", "").lower()
            ]
            if any(var in query_lower for var in poi_variations):
                locations.append(poi)

        return locations
