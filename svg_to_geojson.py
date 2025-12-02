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
name = '251126_Moovle heatmap'
input_svg = f"{name}.svg"
output_json = f"{name}.json"

#Je kan eventueel de resolutie van je shapemap verhogen door hieronder het aantal samples
#te verhogen.
samples = 50
mirrored = True
compression = True

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
    deltas = [x for x in deltas if x != [0,0]]
    return deltas

def deltas_compression(delta):
    if len(delta) <= 4:
        return delta
    deltas = [delta[0]]
    _x = _y = 0
    for index, d in enumerate(delta[1:], start=1):
        cx = d[0]
        cy = d[1]

        if index == len(delta)-1:
            deltas.append([_x + cx,_y + cy])
            break
        nx = delta[index+1][0]
        ny = delta[index+1][1]

        if (cx >= 0 and cy >= 0 and nx >= 0 and ny >= 0) or (cx <= 0 and cy <= 0 and nx <= 0 and ny <= 0):
            if cx == nx == 0:
                _y += cy
                continue
            elif cy == ny == 0:
                _x += cx
                continue
            else:
                deltas.append([_x + cx,_y + cy])
                _x = _y = 0
        else:
            deltas.append([_x + cx,_y + cy])
            _x = _y = 0            
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
        if compression:
            deltas = deltas_compression(deltas)

        arc_index = len(arcs)
        arcs.append(deltas)

        try:
            locationPath = f"""{int(path_elem.attrib.get("id", i+1)):03}"""
        except:
            locationPath = path_elem.attrib.get("id", i+1)

        geometry = {
            "type": "Polygon",
            "arcs": [[arc_index]],
            "properties": {
                "locationPath": f"""{locationPath}""",
                "buildingCode": "WKD"
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
