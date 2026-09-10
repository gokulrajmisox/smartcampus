import osmnx as ox

ox.settings.all_oneway = True
try:
    print('Downloading graph...')
    # Using 800m distance around Sathyabama
    G = ox.graph_from_point((12.8734977, 80.2198655), dist=800, network_type='all', simplify=False, retain_all=True)
    print('Nodes:', len(G.nodes))
    ox.save_graph_xml(G, filepath='attached_assets/sathyabama_small.osm')
    print('Saved to attached_assets/sathyabama_small.osm')
except Exception as e:
    print('Error:', e)
