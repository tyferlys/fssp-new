from fastapi import APIRouter, Depends, Response, status

from src.task.schemas import InputTask, OutputTask
from src.utils.queue.queue import QueueFSSP
from src.utils.queue.schemas import Task

router = APIRouter()


@router.post("/tasks")
async def create_task(priority_task: int, task_input: InputTask) -> OutputTask:
    return await QueueFSSP.put_task(priority_task, task_input)

@router.get("/tasks/{uuid}")
async def get_task(uuid: str, response: Response):
    result: Task = await QueueFSSP.get_task(uuid)

    if result.status_code == 500:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return None
    elif result is None or result == "":
        response.status_code = status.HTTP_404_NOT_FOUND
        return None
    elif result.status_code == 100:
        response.status_code = status.HTTP_202_ACCEPTED
        return None
    elif result.status_code == 400:
        response.status_code = status.HTTP_404_NOT_FOUND
        return None
    else:
        return result.result