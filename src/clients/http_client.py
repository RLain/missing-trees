import aiohttp
from typing import Dict, Any, Optional
from src.utils.api_error import ApiError


class HttpClient:
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.session = aiohttp.ClientSession()

    async def get(self, url: str) -> Dict[str, Any]:
        full_url = f"{self.base_url}/{url.lstrip('/')}"
        async with self.session.get(full_url, headers=self.headers) as response:
            status = response.status
            try:
                body = await response.json()
            except Exception:
                body = {"message": "Unexpected error", "name": "InvalidJSON"}

            if status != 200:
                error_message = body.get("detail") or body.get("message") or f"API returned {status}"
                raise ApiError(
                    status=status,
                    message=error_message,
                    body=body
                )

            return body

    async def close(self):
        await self.session.close()
