import os
import boto3
from botocore.config import Config
from environs import Env

class Environment:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Environment, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.env = Env()
        self.env.read_env()

        self.local = not bool(os.getenv("AWS_EXECUTION_ENV"))
        self.node_env = self._node_env_validator(os.getenv("NODE_ENV"))

        self.s3_client = self._create_s3_client()
        self.sqs_client = self._create_sqs_client()
        self.queue_name = f"middleware-client-bulk-updater-{self.node_env}-process-updates.fifo"
        self.queue_url = self._get_queue_url()

    def _create_s3_client(self):
        if self.local:
            return boto3.client(
                "s3",
                aws_access_key_id="S3RVER",
                aws_secret_access_key="S3RVER",
                endpoint_url="http://localhost:4569",
                config=Config(s3={"addressing_style": "path"}),
                region_name="us-east-1",  # or any default region
            )
        else:
            return boto3.client(
                "s3",
                region_name=os.getenv("AWS_REGION_VARIABLE"),
            )

    def _create_sqs_client(self):
        region = os.getenv("AWS_REGION_VARIABLE")
        if self.local:
            return boto3.client(
                "sqs",
                endpoint_url="http://localhost:9324",
                region_name=region,
            )
        else:
            return boto3.client(
                "sqs",
                endpoint_url=f"https://sqs.af-south-1.amazonaws.com",
                region_name=region,
            )

    def _get_queue_url(self):
        if self.local:
            return "http://localhost:9324/queue/clientBulkUpdates"
        else:
            region = os.getenv("AWS_REGION_VARIABLE")
            account = os.getenv("AWS_ACCOUNT")
            return f"https://sqs.{region}.amazonaws.com/{account}/{self.queue_name}"

    def _node_env_validator(self, value: str) -> str:
        if not value or value.lower() in {"dev", "offline"}:
            return "development"
        return value


# Global singleton instance
environment = Environment()
