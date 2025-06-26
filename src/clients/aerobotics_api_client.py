from typing import Any, Dict, List
from .http_client import HttpClient
from utils.time_utils import start_time_in_ms, log_elapsed_time_in_ms

class AeroboticsAPIClient(HttpClient):
    async def get_survey(self, orchard_id: str) -> Dict[str, Any]:
        url = f"farming/surveys?orchard_id={orchard_id}"
        start = start_time_in_ms()
        survey = await self.get(url=url)
        log_elapsed_time_in_ms(start, f"Get survey {orchard_id}")
        return survey
    
    async def get_tree_survey(self, survey_id: str) -> Dict[str, Any]:
        url = f"farming/surveys/{survey_id}/tree_surveys/"
        start = start_time_in_ms()
        survey = await self.get(url=url)
        log_elapsed_time_in_ms(start, f"Get tree survey {survey_id}")
        return survey

