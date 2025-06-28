import pytest
from src.validation.aerobotics import validate_survey_response, validate_tree_survey_response

@pytest.mark.parametrize("survey, expected_result, expected_error", [
    # Missing results
    ({}, False, "No survey results found"),
    ({"results": []}, False, "No survey results found"),
    ({"results": None}, False, "No survey results found"),
    ({"results": "not a list"}, False, "No survey results found"),

    # Missing 'id' and 'polygon'
    ({"results": [{}]}, False, "Missing 'id' in survey result"),
    ({"results": [{"id": 123}]}, False, "Missing 'polygon' in survey result"),
    ({"results": [{"polygon": "1,2 3,4"}]}, False, "Missing 'id' in survey result"),

    # Wrong types
    ({"results": [{"id": "not-an-int", "polygon": "1,2 3,4"}]}, False, "'id' must be an integer"),
    ({"results": [{"id": 123, "polygon": 456}]}, False, "'polygon' must be a string"),

    # Valid input
    ({"results": [{"id": 123, "polygon": "1,2 3,4 1,2"}]}, True, None),
])
def test_validate_survey_response(survey, expected_result, expected_error):
    result, error = validate_survey_response(survey)
    assert result == expected_result
    assert error == expected_error

@pytest.mark.parametrize("tree_survey, expected_result, expected_error", [
    # Missing or empty results
    ({}, False, "No tree survey results found"),
    ({"results": []}, False, "No tree survey results found"),
    ({"results": None}, False, "No tree survey results found"),
    ({"results": "not a list"}, False, "No tree survey results found"),

    # Missing fields
    ({"results": [{}]}, False, "Missing 'lat' in tree survey result"),
    ({"results": [{"lat": -32.3}]}, False, "Missing 'lng' in tree survey result"),
    ({"results": [{"lat": -32.3, "lng": 18.8}]}, False, "Missing 'area' in tree survey result"),
    ({"results": [{"lat": -32.3, "lng": 18.8, "area": 22.6}]}, False, "Missing 'survey_id' in tree survey result"),

    # Wrong types
    ({"results": [{"lat": "wrong", "lng": 18.8, "area": 22.6, "survey_id": 1}]}, False, "'lat' must be of type float"),
    ({"results": [{"lat": -32.3, "lng": "wrong", "area": 22.6, "survey_id": 1}]}, False, "'lng' must be of type float"),
    ({"results": [{"lat": -32.3, "lng": 18.8, "area": "big", "survey_id": 1}]}, False, "'area' must be of type float"),
    ({"results": [{"lat": -32.3, "lng": 18.8, "area": 22.6, "survey_id": "wrong"}]}, False, "'survey_id' must be of type int"),

    # Valid input
    ({"results": [{"lat": -32.3, "lng": 18.8, "area": 22.6, "survey_id": 123}]}, True, None),
])
def test_validate_tree_survey_response(tree_survey, expected_result, expected_error):
    result, error = validate_tree_survey_response(tree_survey)
    assert result == expected_result
    assert error == expected_error