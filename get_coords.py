import urllib.request
import json
url = 'https://nominatim.openstreetmap.org/search?q=Sathyabama+Institute+of+Science+and+Technology,+Chennai&format=json'
req = urllib.request.Request(url, headers={'User-Agent': 'CampusNavigatorSetup/1.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        if data:
            print(f"Lat: {data[0]['lat']}, Lon: {data[0]['lon']}")
        else:
            print('Not found')
except Exception as e:
    print('Error:', e)
