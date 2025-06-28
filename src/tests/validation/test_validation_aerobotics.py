import pytest
from validation.validation_aerobotics import validate_survey_response

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