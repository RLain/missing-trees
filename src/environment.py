from environs import Env
class Environment:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.env = Env()
        self.env.read_env()

        # Load required env vars here with validation
        self.aerobotics_api_key = self.env.str("AEROBOTICS_API_KEY")
        self.aerobotics_api_base_url = self.env.str("AEROBOTICS_BASE_URL")

        # You can add more env vars as needed

# singleton instance to import
environment = Environment()
