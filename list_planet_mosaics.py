#!/usr/bin/env python3
"""List Planet Basemaps mosaics available to the configured API key."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64

api_key = os.environ.get("PLANET_API_KEY")
if not api_key:
    raise SystemExit("PLANET_API_KEY is not set")

params = {"_page_size": "100"}
url = "https://api.planet.com/basemaps/v1/mosaics/?" + urlencode(params)
token = base64.b64encode(f"{api_key}:".encode()).decode()
request = Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"})

try:
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
except HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    raise SystemExit(f"Planet API returned HTTP {exc.code}: {body[:500]}")
except URLError as exc:
    raise SystemExit(f"Planet API request failed: {exc.reason}")

mosaics = payload.get("mosaics", [])
if not mosaics:
    print("No accessible mosaics were returned for this API key.")
    print("This may mean the account lacks Basemaps/Mosaics access or has no matching Area of Access.")
    raise SystemExit(0)

print(f"Found {len(mosaics)} accessible mosaic(s):\n")
for mosaic in mosaics:
    bbox = mosaic.get("bbox") or []
    print(f"ID: {mosaic.get('id', 'N/A')}")
    print(f"Name: {mosaic.get('name', 'N/A')}")
    print(f"Product: {mosaic.get('product_type', 'N/A')}")
    print(f"Coverage bbox: {bbox}")
    print(f"First acquired: {mosaic.get('first_acquired', 'N/A')}")
    print(f"Last acquired: {mosaic.get('last_acquired', 'N/A')}")
    print(f"Tile link: {(mosaic.get('_links') or {}).get('tiles', 'N/A')}")
    print("-")
