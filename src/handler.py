from clients.aerobotics_api_client import AeroboticsAPIClient
from utils.helpers import convert_result_to_analysis, orchard_result_to_dict
from validation.aerobotics import (
    validate_survey_response,
    validate_tree_survey_response,
)
from utils.api_error import ApiError
from utils.visualisation import create_orchard_map
from utils.spatial import (
    build_outer_polygon_from_survey,
    create_tree_polygons,
    find_missing_tree_positions,
    inner_boundary_visualisation,
)
import asyncio
from clients.aerobotics_api_client import AeroboticsAPIClient
import json

# TODO: Pass into API
orchard_id = "216269"

async def missing_trees(event, context):
    # TODO: Continue with when focusing on deployment - 404 is working
    # {RL 28/06/2025} Without an orchard_id, get_survey returns multiple surveys for different farms
    # orchard_id = None
    # if "pathParameters" in event and event["pathParameters"]:
    #     orchard_id = event["pathParameters"].get("orchard_id")

    # if not orchard_id:
    #     return {
    #         "statusCode": 404,
    #         "body": '{"error": "orchard_id path parameter is required"}',
    #         "headers": {
    #             "Content-Type": "application/json"
    #         }
    #     }

    client = AeroboticsAPIClient()
    try:
        survey = await client.get_survey(orchard_id)
        valid, error_msg = validate_survey_response(survey)
        if not valid:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "error": f"The upstream data source did not return required fields: {error_msg}"
                    }
                ),
                "headers": {"Content-Type": "application/json"},
            }

        survey_id = survey["results"][0]["id"]

        tree_survey = await client.get_tree_survey(survey_id)
        valid, error_msg = validate_tree_survey_response(tree_survey)
        if not valid:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "error": f"The upstream data source did not return required fields: {error_msg}"
                    }
                ),
                "headers": {"Content-Type": "application/json"},
            }

        tree_data = [
            {
                "lat": tree["lat"],
                "lng": tree["lng"],
                "area": tree["area"],
            }
            for tree in tree_survey["results"]
        ]

        outer_polygon = build_outer_polygon_from_survey(survey)
        results = find_missing_tree_positions(tree_data, outer_polygon)
        inner_boundary_geographic = inner_boundary_visualisation(outer_polygon)
        tree_polygons = create_tree_polygons(tree_data)

        #  {RL 28/06/2025} Purely for developer to help debug with visualization
        folium_map = create_orchard_map(
            tree_polygons=tree_polygons,
            outer_polygon=outer_polygon,
            inner_boundary=inner_boundary_geographic,
            missing_points=results["missing_coords"],
        )
        output_path = "/tmp/tree_gaps_map.html"
        folium_map.save(output_path)

        result_to_analysis = convert_result_to_analysis(results)
        
        return orchard_result_to_dict(result_to_analysis)

    except ApiError as e:
        return {
            "statusCode": e.status,
            "body": json.dumps({"error": {"message": e.message, "status": e.status}}),
            "headers": {"Content-Type": "application/json"},
        }

    finally:
        await client.close()


# For local testing
if __name__ == "__main__":
    import sys

    event = {"orchard_id": orchard_id}
    context = {}

    result = asyncio.run(missing_trees(event, context))
    print("Lambda handler result:", result)
