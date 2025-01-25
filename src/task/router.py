from fastapi import APIRouter, Depends

from src.task.schemas import InputTask
from src.task.service import TaskService

router = APIRouter()


@router.get("/")
def create_task(
        input_task: InputTask,
        task_service: TaskService = Depends(TaskService),
):
    return task_service.create_task(input_task)