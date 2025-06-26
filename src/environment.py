import os
import boto3
from botocore.config import Config
from environs import Env
class Environment:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Environment, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.env = Env()
        self.env.read_env()

        self.aerobotics_api_key = os.getenv("AEROBOTICS_API_KEY")
        self.aerobotics_api_base_url = os.getenv("AEROBOTICS_API_BASE_URL")

environment = Environment()
