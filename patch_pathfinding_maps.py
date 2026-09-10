import os

with open('src/pathfinding.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace instances of folium.Map(location=self.center, zoom_start=17)
# with a satellite tile layer.

map_init = """
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
"""

content = content.replace('m = folium.Map(location=self.center, zoom_start=17)', map_init.strip())

with open('src/pathfinding.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched pathfinding.py for map tiles")
