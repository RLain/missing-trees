import requests
from src.utils.api_error import ApiError
from src.utils.time_utils import start_time_in_ms, log_elapsed_time_in_ms


class AeroboticsAPIClient:
    def __init__(self, bearer_token: str):
        self.base_url = "https://api.aerobotics.com"
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }

    def _request(self, endpoint: str, description: str) -> dict:
        start = start_time_in_ms()
        url = f"{self.base_url}/{endpoint}"
        print(f"** GET : {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            
            try:
                body = response.json()
            except Exception:
                body = {"message": "Invalid JSON response"}

            if response.status_code != 200:
                error_message = body.get("detail") or body.get("message") or f"API returned {response.status_code}"
                raise ApiError(status=response.status_code, message=error_message, body=body)

            return body
        finally:
            log_elapsed_time_in_ms(start, description)

    def get_survey(self, orchard_id: str) -> dict:
        return self._request(f"farming/surveys?orchard_id={orchard_id}", f"Get survey {orchard_id}")

    def get_tree_survey(self, survey_id: str) -> dict:
        return self._request(f"farming/surveys/{survey_id}/tree_surveys/", f"Get tree survey {survey_id}")