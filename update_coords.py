import json
import random

base_lat = 12.8735
base_lon = 80.2198

with open('campus_data/demo_locations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for loc in data['locations']:
    lat_offset = random.uniform(-0.003, 0.003)
    lon_offset = random.uniform(-0.003, 0.003)
    
    if loc['id'] == 'main_gate':
        lat_offset = -0.002
        lon_offset = -0.001
    elif loc['id'] == 'library':
        lat_offset = 0.001
        lon_offset = 0.001
        
    loc['coordinates']['lat'] = round(base_lat + lat_offset, 5)
    loc['coordinates']['lng'] = round(base_lon + lon_offset, 5)

with open('campus_data/demo_locations.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print('Updated demo_locations.json with new coordinates.')
