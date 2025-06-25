import aiohttp
import asyncio
from environment import environment

class HttpClient:
    def __init__(self):
        self.aerobotics_api_base_url = environment.env("AEROBOTICS_BASE_URL")
        self.aerobotics_api_key = environment.env("AEROBOTICS_API_KEY")
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.aerobotics_api_key}",
            "Content-Type": "application/json"
        }

    async def get(self, url: str, json: bool = True):
        full_url = f"{self.aerobotics_api_base_url}{url}"
        print(f"** GET : HTTPClient URL: {full_url}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(full_url, headers=self.headers) as response:
                    if json:
                        try:
                            return await response.json()
                        except Exception as err:
                            print(err)
                            print("GET : response could not be converted to JSON", response)
            except Exception as err:
                print("Fetch GET request failed.")
                print(err)
