import os
from functools import lru_cache
from typing import Any

from pydantic.v1 import BaseSettings
from dotenv import find_dotenv


class Settings(BaseSettings):
    queue_for_tasks_input: str
    queue_for_tasks_output: str

    rabbitmq_login: str
    rabbitmq_password: str
    rabbitmq_host: str

    def __init__(self, **values: Any):
        super().__init__(**values)
        for attribute, value in self.__dict__.items():
            self.__dict__[attribute] = os.getenv(attribute, value)
            pass

    class Config:
        env_file = find_dotenv(".env")


@lru_cache()
def get_settings():
    return Settings()