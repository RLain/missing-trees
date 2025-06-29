from typing import Any, Dict
from src.utils.api_error import ApiError
from .http_client import HttpClient
from src.utils.time_utils import start_time_in_ms, log_elapsed_time_in_ms
from src.config.environment import environment


class AeroboticsAPIClient(HttpClient):
    def __init__(self, bearer_token: str):
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }
        super().__init__(base_url="https://api.aerobotics.com/", headers=headers)

    async def get_survey(self, orchard_id: str):
        url = f"farming/surveys?orchard_id={orchard_id}"
        start = start_time_in_ms()

        full_url = f"{self.base_url}/{url}"
        print(f"** GET : HTTPClient URL: {full_url}")

        try:
            survey = await self.get(url)
        except ApiError as e:
            log_elapsed_time_in_ms(start, f"Get survey {orchard_id}")
            detail = e.body.get("detail") or e.body.get("message") or str(e.body)
            raise ApiError(status=e.status, message=detail, body=e.body)
        else:
            log_elapsed_time_in_ms(start, f"Get survey {orchard_id}")
            return survey

    async def get_tree_survey(self, survey_id: str) -> Dict[str, Any]:
        url = f"farming/surveys/{survey_id}/tree_surveys/"
        start = start_time_in_ms()

        full_url = f"{self.base_url}/{url}"
        print(f"** GET : HTTPClient URL: {full_url}")

        try:
            survey = await self.get(url)
        except ApiError as e:
            log_elapsed_time_in_ms(start, f"Get tree survey {survey_id}")
            detail = e.body.get("detail") or e.body.get("message") or str(e.body)
            raise ApiError(status=e.status, message=detail, body=e.body)
        else:
            log_elapsed_time_in_ms(start, f"Get tree survey {survey_id}")
            return survey
