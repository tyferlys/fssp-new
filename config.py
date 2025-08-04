import os
from functools import lru_cache
from typing import Any

import loguru
from pydantic.v1 import BaseSettings
from dotenv import find_dotenv


class Settings(BaseSettings):
    proxy_host: str


    def __init__(self, **values: Any):
        super().__init__(**values)
        try:
            self.proxy_host = os.environ["PROXY_HOST"]
        except Exception as e:
            # loguru.logger.exception(e)
            pass

    class Config:
        env_file = find_dotenv(".env")


@lru_cache()
def get_settings():
    return Settings()