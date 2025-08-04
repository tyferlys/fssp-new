from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.task.schemas import InputTask


class Task(BaseModel):
    uuid: str
    priority: int
    datetime_ready: Optional[datetime] = None
    result: Optional[dict | str] = None
    status_code: int
    task_data: InputTask

class State(BaseModel):
    started: bool
    tasks: list