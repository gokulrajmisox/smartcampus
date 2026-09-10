import os

with open('src/pathfinding.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We want find_path to use self.create_base_map() instead of rebuilding the map from scratch.
# The code in find_path currently does:
old_map_init = """
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
"""

new_map_init = """
        m = self.create_base_map()
"""

# Replace all occurrences of old_map_init. It will match the one in find_path.
# Wait, create_base_map also has this!
# We don't want to replace the one in create_base_map.
# Let's split by 'def find_path'
parts = content.split('def find_path(self, start_name: str, end_name: str, algorithm: str, accessibility_mode: bool = False) -> Dict[str, Any]:')

if len(parts) == 2:
    parts[1] = parts[1].replace(old_map_init.strip('\n'), new_map_init.strip('\n'))
    with open('src/pathfinding.py', 'w', encoding='utf-8') as f:
        f.write('def find_path(self, start_name: str, end_name: str, algorithm: str, accessibility_mode: bool = False) -> Dict[str, Any]:'.join(parts))
    print("Patched find_path")
else:
    print("Could not find find_path signature")
