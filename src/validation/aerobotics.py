def validate_survey_response(survey: dict) -> tuple[bool, str | None]:
    results = survey.get("results")
    if not results or not isinstance(results, list) or len(results) == 0:
        return False, "No survey results found"

    first_result = results[0]
    survey_id = first_result.get("id")
    polygon = first_result.get("polygon")

    if not survey_id:
        return False, "Missing 'id' in survey result"
    if not polygon:
        return False, "Missing 'polygon' in survey result"
    if not isinstance(survey_id, int):
        return False, "'id' must be an integer"
    if not isinstance(polygon, str):
        return False, "'polygon' must be a string"

    return True, None


def validate_tree_survey_response(tree_survey: dict) -> tuple[bool, str | None]:
    results = tree_survey.get("results")
    if not results or not isinstance(results, list) or len(results) == 0:
        return False, "No tree survey results found"

    first_result = results[0]
    required_fields = {
        "lat": float,
        "lng": float,
        "area": float,
        "survey_id": int,
    }

    for field, expected_type in required_fields.items():
        value = first_result.get(field)
        if value is None:
            return False, f"Missing '{field}' in tree survey result"
        if not isinstance(value, expected_type):
            return False, f"'{field}' must be of type {expected_type.__name__}"

    return True, None


