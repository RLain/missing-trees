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
        # {RL 29/06/2025} No longer in use - keeping in as an example of an environment set up
        self.aerobotics_api_key = self.env.str("AEROBOTICS_API_KEY")


environment = Environment()

