from utils.visualisation import create_map
from utils.spatial import create_tree_polygons
from shapely.geometry import Polygon
from shapely.ops import unary_union
import pandas as pd
import geopandas as gpd
import math

# Your existing outer_polygon and other logic here...

def missing_trees(event, context):
    print("Initiation: Reached missing trees")
    # Example tree data, replace with real input from event or elsewhere
    trees = [{"lat": -32.3, "lng": 18.8, "area": 20}, {"lat": -32.31, "lng": 18.81, "area": 25}]

    tree_polygons = create_tree_polygons(trees)
    
    print("Passed: Created tree_polygons")


    # Suppose you have outer_polygon and gap_polygons computed as before
    # (copy or import the polygon definitions as needed)
    
    # For demo, recreate your outer polygon here:
    coord_str = "18.825688993836707,-32.32741477565738 18.82707301368839,-32.32771395090236 18.82696840753681,-32.32805392157161 18.826920127774542,-32.32810831676022 18.82668945779926,-32.328899309768175 18.82535103550083,-32.32913728625483 18.825165963078803,-32.32913048693532 18.825688993836707,-32.32741477565738"
    coords = [(float(lng), float(lat)) for lng, lat in (pair.split(',') for pair in coord_str.split())]
    assert coords[0] == coords[-1], "Polygon ring must be closed"
    outer_polygon = Polygon(coords)

    trees_union = unary_union(tree_polygons)
    gaps = outer_polygon.difference(trees_union)

    gap_polygons = []
    from shapely.geometry import MultiPolygon, Polygon as ShapelyPolygon
    if isinstance(gaps, ShapelyPolygon):
        if gaps.area > 10:
            gap_polygons.append(gaps)
    elif isinstance(gaps, MultiPolygon):
        gap_polygons = [g for g in gaps.geoms if g.area > 10]

    # Create folium map
    folium_map = create_map(tree_polygons, outer_polygon, gap_polygons)

    # Save map to HTML file (you can adjust this path)
    output_path = "/tmp/tree_gaps_map.html"
    folium_map.save(output_path)

    return {
        "statusCode": 200,
        "body": f"Map generated and saved to {output_path}"
    }


if __name__ == "__main__":
    response = missing_trees({}, {})
    print(response)
