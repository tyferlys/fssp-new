from datetime import date

from pydantic import BaseModel


class InputTask(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    birth_date: str

class OutputTask(BaseModel):
    uuid: str