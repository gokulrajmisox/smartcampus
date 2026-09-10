import re
import os

with open('src/pathfinding.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add is_edge_accessible method
accessible_method = """
    def is_edge_accessible(self, u: int, v: int) -> bool:
        \"\"\"Check if an edge is wheelchair accessible.\"\"\"
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

    def bfs_osm"""
content = content.replace('    def bfs_osm', accessible_method)

# Update signatures
funcs = ['bfs_osm', 'dfs_osm', 'ucs_osm', 'astar_euclidean', 'astar_manhattan', 'astar_combined', 'astar_osm']
for func in funcs:
    content = re.sub(rf'def {func}\(self, start: int, end: int\)',
                     rf'def {func}(self, start: int, end: int, accessibility_mode: bool = False)', content)

# Update find_path signature and calls
find_path_sig = 'def find_path(self, start_name: str, end_name: str, algorithm: str)'
new_find_path_sig = 'def find_path(self, start_name: str, end_name: str, algorithm: str, accessibility_mode: bool = False)'
content = content.replace(find_path_sig, new_find_path_sig)

# Replace the calls in find_path
for func in funcs:
    content = re.sub(rf'self\.{func}\(start_node, end_node\)',
                     rf'self.{func}(start_node, end_node, accessibility_mode)', content)

# Now inject the accessibility check in the neighbor loops.
# First, let's look at the standard neighbor loops.
# We'll use a regex that matches `for nbr in self.graph.neighbors(var):`
# and inserts the check.
content = re.sub(r'(for nbr in self\.graph\.neighbors\(([^)]+)\):)',
                 r'\1\n                    if accessibility_mode and not self.is_edge_accessible(\2, nbr):\n                        continue', content)

# Need to fix indentation if we inject, but `continue` works. Wait, some loops might not have 20 spaces indentation, but python is fine if we use 4 spaces relative to `for` or just rely on regex properly.
# A safer way: replace `for nbr in self.graph.neighbors(node):` with:
# for nbr in self.graph.neighbors(node):
#     if accessibility_mode and not self.is_edge_accessible(node, nbr): continue

def replace_neighbor_loop(match):
    indent = match.group(1)
    var = match.group(2)
    return f"{indent}for nbr in self.graph.neighbors({var}):\n{indent}    if accessibility_mode and not self.is_edge_accessible({var}, nbr): continue"

content = re.sub(r'^(\s*)for nbr in self\.graph\.neighbors\(([^)]+)\):', replace_neighbor_loop, content, flags=re.MULTILINE)

with open('src/pathfinding.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched pathfinding.py")
