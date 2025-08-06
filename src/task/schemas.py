from datetime import date

from pydantic import BaseModel


class HealthCheckStatus(BaseModel):
    status: bool


class InputTask(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    birth_date: str

class OutputTask(BaseModel):
    uuid: str