"""Script dat een vectorbestand met verschillende paden omzet naar een GeoJson bestand.

Returns:
    Json bestand
"""

import xml.etree.ElementTree as ET
from svgpathtools import parse_path
import json


""" Settings """
#Zet je vector bestand in de zelfde map als dit script en vul hieronder te naam van het bestand in
#onder 'name', zonder extentie!
name = 'body'
input_svg = f"{name}.svg"
output_json = f"{name}.json"

#Je kan eventueel de resolutie van je shapemap verhogen door hieronder het aantal samples
#te verhogen.
samples = 50
mirrored = True

def bezier_to_points(path_str, samples=50):
    path = parse_path(path_str)
    points = []
    for segment in path:
        for i in range(samples + 1):
            t = i / samples
            point = segment.point(t)
            x = round(point.real)
            y = round(-point.imag if mirrored else point.imag)
            points.append([x, y])
            # points.append([round(point.real), round(point.imag)])
    return points

def points_to_deltas(points):
    if not points:
        return []
    deltas = [points[0]]
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        deltas.append([dx, dy])
    return deltas

def svg_to_topology(svg_file, samples=50):
    tree = ET.parse(svg_file)
    root = tree.getroot()
    namespace = {'svg': 'http://www.w3.org/2000/svg'}
    
    arcs = []
    geometries = []

    for i, path_elem in enumerate(root.findall('.//svg:path', namespace)):
        d = path_elem.attrib.get('d')
        if not d:
            continue
        points = bezier_to_points(d, samples)
        
        # Sluit polygon
        if points[0] != points[-1]:
            points.append(points[0])

        deltas = points_to_deltas(points)
        arc_index = len(arcs)
        arcs.append(deltas)

        geometry = {
            "type": "Polygon",
            "arcs": [[arc_index]],
            "properties": {
            "name": path_elem.attrib.get("id", f"unnamed_{i+1}")
            },
            # "properties": {
            #     "buildingCode": path_elem.attrib.get("data-code", "UNKNOWN"),
            #     "locationPath": path_elem.attrib.get("data-location", f"ZONE_{i+1}")
            # }
        }
        geometries.append(geometry)

    topology = {
        "type": "Topology",
        "arcs": arcs,
        "transform": {
            "scale": [1e-6, 1e-6],
            "translate": [0, 0]
        },
        "objects": {
            "continents": {
                "type": "GeometryCollection",
                "geometries": geometries
            }
        }
    }

    return topology

if __name__ == "__main__":

    topo = svg_to_topology(input_svg, samples=samples)

    with open(output_json, "w") as f:
        json.dump(topo, f, indent=2)

    print(f"✅ Topology opgeslagen in '{output_json}'")
