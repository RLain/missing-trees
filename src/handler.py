from clients.aerobotics_api_client import AeroboticsAPIClient
from utils.visualisation import create_map
from utils.spatial import create_tree_polygons, find_missing_tree_gaps
from shapely.geometry import Polygon
from shapely.ops import unary_union
import pandas as pd
import geopandas as gpd
import asyncio
from pathlib import Path
from clients.aerobotics_api_client import AeroboticsAPIClient
from utils.spatial import create_tree_polygons, find_missing_tree_gaps
import json

#TODO: Pass into API
orchard_id="216269"

async def missing_trees(event, context):
    # TODO: Return orchard_id = event.get("orchard_id", "216269")

    client = AeroboticsAPIClient()
    
    survey = await client.get_survey(orchard_id)
    
    coords = [(float(lng), float(lat)) for lng, lat in (pair.split(',') for pair in survey["results"][0]["polygon"].split())]
    assert coords[0] == coords[-1], "Polygon ring must be closed"
    outer_polygon = Polygon(coords)
    
    survey_id = survey["results"][0]["id"]
    json_path = Path(__file__).parent / "tree_survey_data.json"

    # To stop me unecessarily invoking the API as the dummy data is not changing
    if json_path.exists() and json_path.stat().st_size > 0:
        with open(json_path) as f:
            tree_survey = json.load(f)
    else:
        tree_survey = await client.get_tree_survey(survey_id)
        with open(json_path, "w") as f:
            json.dump(tree_survey, f, indent=2)
    
    tree_data = [
        {
            "lat": tree["lat"],
            "lng": tree["lng"],
            "area": tree["area"],
        }
        for tree in tree_survey["results"]
    ]

    #TODO: Add error handling to end if no tree data is returning
    tree_polygons = create_tree_polygons(tree_data)
    gaps = find_missing_tree_gaps(outer_polygon, tree_polygons)

    print("gap polygons returned by find_missing_tree_gaps:", gaps)

    # Use gaps directly, since they're already filtered
    for i, gap in enumerate(gaps):
        print(f"Gap {i} area (m²): {gap.area}")

    folium_map = create_map(tree_polygons, outer_polygon, gaps)

    # Save map to HTML file (you can adjust this path)
    output_path = "/tmp/tree_gaps_map.html"
    folium_map.save(output_path)

    # Example return: number of trees and gaps found
    return {
        "tree_count": len(tree_polygons),
        "gap_count": len(gaps),
        #"gaps": [gap.wkt for gap in gaps],
    }


# For local testing
if __name__ == "__main__":
    import sys

    event = {"orchard_id": orchard_id}
    context = {}

    result = asyncio.run(missing_trees(event, context))
    print("Lambda handler result:", result)
