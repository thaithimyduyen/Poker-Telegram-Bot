import os


class Config:
    def __init__(self):
        self.REDIS_HOST: str = os.getenv(
            "POKERBOT_REDIS_HOST",
            default="localhost",
        )
        self.REDIS_PORT: str = int(os.getenv(
            "POKERBOT_REDIS_PORT",
            default="6379"
        ))
        self.REDIS_PASS: str = os.getenv(
            "POKERBOT_REDIS_PASS",
            default="",
        )
        self.REDIS_DB: int = int(os.getenv(
            "POKERBOT_REDIS_DB",
            default="0"
        ))
        self.TOKEN: str = os.getenv(
            "POKERBOT_TOKEN",
            default="",
        )
        self.DEBUG: bool = bool(os.getenv(
            "POKERBOT_DEBUG",
            default="0"
        ) == "1")
