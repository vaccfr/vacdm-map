import argparse, re, requests
from geojson import Feature, FeatureCollection, Polygon, dump

def convert_cordinates(coords):
    match = re.match(r"([NS])(\d{3})\.(\d{2})\.(\d{2})\.(\d{3}):([EW])(\d{3})\.(\d{2})\.(\d{2})\.(\d{3})", coords)
    if not match:
        raise ValueError("Invalid coordinate format")
    
    lat_sign = 1 if match.group(1) == 'N' else -1
    lon_sign = 1 if match.group(6) == 'E' else -1
    
    latitude = lat_sign * (int(match.group(2)) + int(match.group(3))/60 + int(match.group(4))/3600 + int(match.group(5))/3600000)
    longitude = lon_sign * (int(match.group(7)) + int(match.group(8))/60 + int(match.group(9))/3600 + int(match.group(10))/3600000)
    
    return (longitude, latitude)

def generate_geojson_polygon(coord_list):
    coord_list.append(coord_list[0])
    coordinates = [convert_cordinates(coord) for coord in coord_list]
    return Polygon([coordinates])

parser = argparse.ArgumentParser(description="Generate GeoJSON file for VATSIM VACDM map")
parser.add_argument("-a", "--api-url", help="VACDM endpoint URL", default="https://cdm.vatsim.fr")
parser.add_argument("-o", "--output-file", help="Output file name", default="vacdm_map.geojson")
args = parser.parse_args()

url = args.api_url + "/api/v1/airports"
print(f"Fetching data from {url}")
try:
    response = requests.get(url)
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print(f"{err}")
    exit(1)
airports = response.json()

features = []
for airport in airports:
    airport_icao = airport["icao"].upper()
    print(airport_icao)
    for taxizone in airport["taxizones"]:
        print(f"    {taxizone['label']}")
        properties = {
            "icao": airport_icao,
            "label": taxizone['label'],
            "taxiout": taxizone['taxiout']
        }
        for taxitime in taxizone["taxitimes"]:
            print(f"        {taxitime['rwy_designator']}: {taxitime['minutes']}")
            properties[taxitime['rwy_designator']] = taxitime['minutes']
        polygon = generate_geojson_polygon(taxizone['polygon'])
        feature = Feature(geometry=polygon, properties=properties)
        features.append(feature)

feature_collection = FeatureCollection(features)
print(f"Write GEOJSON to {args.output_file}")
with open(args.output_file, "w") as file:
    dump(feature_collection, file, sort_keys=False, indent=2)
