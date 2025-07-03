from flask import Flask, request, jsonify
from functools import wraps
import asyncio
import logging
import os
import sys

print("Starting Flask app...", file=sys.stdout, flush=True)

try:
    from src.clients.aerobotics_api_client import AeroboticsAPIClient
    from src.utils.helpers import convert_result_to_analysis, orchard_result_to_dict
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
    print("All imports successful", file=sys.stdout, flush=True)
except Exception as e:
    print(f"Import failed: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create the Flask app
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

print("Flask app created", file=sys.stdout, flush=True)

# AWS environment check should be AFTER app creation
if os.environ.get('AWS_EXECUTION_ENV') or os.environ.get('AWS_REGION'):
    print("AWS environment detected, adding startup buffer...")
    import time
    time.sleep(10)
    print("Startup buffer complete")

def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

def extract_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    return auth_header.replace('Bearer ', '')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/orchards/<orchard_id>/missing-trees', methods=['GET'])
@async_route
async def missing_trees(orchard_id: str):
    app.logger.info(f"Missing tree endpoint invoked for orchard: {orchard_id}")
    
    bearer_token = extract_bearer_token()
    if not bearer_token:
        return jsonify({"error": "Bearer token required"}), 401

    app.logger.info("Setting up AeroboticsAPIClient and invoking API...")
    client = AeroboticsAPIClient(bearer_token)
    
    try:
        # Get survey data
        survey = await client.get_survey(orchard_id)
        valid, error_msg = validate_survey_response(survey)
        if not valid:
            return jsonify({
                "error": f"The upstream data source did not return required fields: {error_msg}"
            }), 500

        survey_id = survey["results"][0]["id"]

        # Get tree survey data
        tree_survey = await client.get_tree_survey(survey_id)
        valid, error_msg = validate_tree_survey_response(tree_survey)
        if not valid:
            return jsonify({
                "error": f"The upstream data source did not return required fields: {error_msg}"
            }), 500

        # Process tree data
        tree_data = [
            {
                "lat": tree["lat"],
                "lng": tree["lng"],
                "area": tree["area"],
            }
            for tree in tree_survey["results"]
        ]

        app.logger.info("Kicking off spatial calculations...")
        app.logger.info("...Creating outer polygon")
        outer_polygon = build_outer_polygon_from_survey(survey)
        
        app.logger.info("...Creating inner boundary")
        inner_boundary_geographic = inner_boundary_visualisation(outer_polygon)
        
        app.logger.info("...Creating tree polygons")
        tree_polygons = create_tree_polygons(tree_data)
        
        app.logger.info("...Finding missing trees")
        results = find_missing_tree_positions(tree_data, outer_polygon)

        app.logger.info("Creating orchard map...")
        # {RL 28/06/2025} Purely for developer to help debug with visualization
        folium_map = create_orchard_map(
            tree_polygons=tree_polygons,
            outer_polygon=outer_polygon,
            inner_boundary=inner_boundary_geographic,
            missing_points=results["missing_coords"],
        )
        
        output_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"tree_gaps_map_{orchard_id}.html")
        folium_map.save(output_path)

        app.logger.info("Analysing results...")
        result_to_analysis = convert_result_to_analysis(results)
        orchard_results_dict = orchard_result_to_dict(result_to_analysis)

        app.logger.info("Returning 200 OK")
        return jsonify(orchard_results_dict), 200

    except ApiError as e:
        return jsonify({
            "error": {
                "message": e.message, 
                "status": e.status
            }
        }), e.status
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            "error": {
                "message": "Internal server error",
                "status": 500
            }
        }), 500

    finally:
        await client.close()


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

print("App setup complete", file=sys.stdout, flush=True)