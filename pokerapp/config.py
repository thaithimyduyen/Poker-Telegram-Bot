import os


class Config:
    REDIS_HOST: str = os.getenv("POKERBOT_REDIS_HOST", default="localhost")
    REDIS_PORT: str = int(os.getenv("POKERBOT_REDIS_PORT", default="6379"))
    REDIS_PASS: str = os.getenv("POKERBOT_REDIS_PASS", default="")
    REDIS_DB: int = int(os.getenv("POKERBOT_REDIS_DB", default="0"))
    TOKEN: str = os.getenv("POKERBOT_TOKEN", default="")
    DEBUG: bool = bool(os.getenv("POKERBOT_DEBUG", default="0") == "1")
