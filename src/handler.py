from clients.aerobotics_api_client import AeroboticsAPIClient
from utils.visualisation import create_orchard_map
from utils.spatial import create_missing_tree_polygons, create_tree_polygons, find_missing_tree_positions
from shapely.geometry import Polygon
import asyncio
from pathlib import Path
from clients.aerobotics_api_client import AeroboticsAPIClient
import json

#TODO: Pass into API
orchard_id="216269"

async def missing_trees(event, context):
    # TODO: Return orchard_id = event.get("orchard_id", "216269")
    # TODO: If orchard_id does not exist return 404 

    client = AeroboticsAPIClient()
    
    survey = await client.get_survey(orchard_id)
    # TODO: Directly return Aerobotics error if no 200 OK 

    
    coords = [(float(lng), float(lat)) for lng, lat in (pair.split(',') for pair in survey["results"][0]["polygon"].split())]
    assert coords[0] == coords[-1], "Polygon ring must be closed"
    outer_polygon = Polygon(coords)
    
    survey_id = survey["results"][0]["id"]
    json_path = Path(__file__).parent / "tree_survey_data.json"

    # INFO: To stop me unecessarily invoking the API for the 508 elements as the dummy data is not changing
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
    tree_points = [(poly.centroid.y, poly.centroid.x) for poly in tree_polygons]
    
    results = find_missing_tree_positions(tree_data, outer_polygon)

    # Create visualization
    folium_map = create_orchard_map(
        tree_polygons=tree_polygons,
        outer_polygon=outer_polygon,
        labeled_points=results["labeled_tree_coords"],
        tree_points=results["tree_points"],
        missing_points=results["missing_coords"],
        matched_trees=results.get("matched_trees", [])
    )

    # Save map to HTML file (you can adjust this path)
    output_path = "/tmp/tree_gaps_map.html"
    folium_map.save(output_path)

    # Example return: number of trees and gaps found
    return {
        "tree_count": len(tree_polygons),
        #"gap_count": len(results["missing_coords"].length),
        #"gaps": [gap.wkt for gap in gaps],
    }


# For local testing
if __name__ == "__main__":
    import sys

    event = {"orchard_id": orchard_id}
    context = {}

    result = asyncio.run(missing_trees(event, context))
    print("Lambda handler result:", result)
