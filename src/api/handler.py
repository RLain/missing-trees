from src.clients.aerobotics_api_client import AeroboticsAPIClient
from src.utils.helpers import convert_result_to_analysis, orchard_result_to_dict
from src.utils.time_utils import log_elapsed_time_in_ms, start_time_in_ms
from src.validation.aerobotics import (
    validate_survey_response,
    validate_tree_survey_response,
)
from src.utils.api_error import ApiError
from src.utils.visualisation import create_orchard_map
from src.utils.spatial import (
    build_outer_polygon_from_survey,
    create_tree_polygons,
    find_missing_tree_positions,
    inner_boundary_visualisation,
)
import asyncio
import json


def missing_trees(event, context):
    print("Missing tree handler invoked...")
    return asyncio.run(missing_trees_async(event, context))


async def missing_trees_async(event, context):
    headers = event.get('headers', {})
    bearer_token = headers.get('Authorization', '').replace('Bearer ', '')
    orchard_id = None

    if not bearer_token:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Bearer token required"}),
        }

    if "pathParameters" in event and event["pathParameters"]:
        orchard_id = event["pathParameters"].get("orchard_id")

    # {RL 28/06/2025} Without an orchard_id, get_survey returns multiple surveys for different farms
    if not orchard_id:
        return {
            "statusCode": 400,
            "body": '{"error": "orchard_id path parameter is required"}',
            "headers": {
                "Content-Type": "application/json"
            }
        }

    print("Setting up AeroboticsAPIClient and invoking API...")
    client = AeroboticsAPIClient(bearer_token)
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

        print("Kicking off spatial calculations...")
        print("...Creating outer polygon")
        outer_polygon = build_outer_polygon_from_survey(survey)
        print("...Creating inner boundary")
        inner_boundary_geographic = inner_boundary_visualisation(outer_polygon)
        print("...Creating tree polygons")
        tree_polygons = create_tree_polygons(tree_data)
        print("...Finding missing trees")
        start = start_time_in_ms()
        results = find_missing_tree_positions(tree_data, outer_polygon)
        log_elapsed_time_in_ms(start, f"Processed find_missing_tree_positions")

        print("Creating orchard map...")
        #  {RL 28/06/2025} Purely for developer to help debug with visualization
        folium_map = create_orchard_map(
            tree_polygons=tree_polygons,
            outer_polygon=outer_polygon,
            inner_boundary=inner_boundary_geographic,
            missing_points=results["missing_coords"],
        )
        output_path = "/tmp/tree_gaps_map.html"
        folium_map.save(output_path)

        print("Analysing results...")
        result_to_analysis = convert_result_to_analysis(results)
        orchard_results_dict = orchard_result_to_dict(result_to_analysis)

        print("Returning 200 OK")
        return {
            "statusCode": 200,
            "body": json.dumps(orchard_results_dict)
        }

    except ApiError as e:
        return {
            "statusCode": e.status,
            "body": json.dumps({"error": {"message": e.message, "status": e.status}}),
            "headers": {"Content-Type": "application/json"},
        }

    finally:
        await client.close()

