class ApiError(Exception):
    def __init__(self, status: int, message: str, body: dict = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.body = body or {}

    def __str__(self):
        return f"{self.__class__.__name__}({self.status}): {self.message}"

    @staticmethod
    def serialize(error: "ApiError") -> dict:
        return {
            "__class": error.__class__.__name__,
            "status": error.status,
            "message": error.message,
        }

    @staticmethod
    def deserialize(data: dict) -> "ApiError":
        if data.get("__class") != ApiError.__name__:
            raise ValueError(f"Cannot deserialize object that is not a {ApiError.__name__}")
        return ApiError(status=data.get("status", 500), message=data.get("message", "Invalid API request"))
