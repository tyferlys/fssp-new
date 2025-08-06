import asyncio
from asyncio import Semaphore

from fastapi import APIRouter, Depends, Response, status

from src.task.schemas import InputTask, OutputTask, HealthCheckStatus
from src.utils.queue.queue import QueueFSSP
from src.utils.queue.schemas import Task

router = APIRouter()
semaphore: Semaphore = Semaphore(1)

@router.post("/tasks")
async def create_task(priority_task: int, task_input: InputTask) -> OutputTask:
    async with semaphore:
        return await QueueFSSP.put_task(priority_task, task_input)

@router.get("/tasks/{uuid}")
async def get_task(uuid: str, response: Response):
    async with semaphore:
        result: Task = await QueueFSSP.get_task(uuid)

        if result is None or result == "":
            response.status_code = status.HTTP_404_NOT_FOUND
            return None
        if result.status_code == 500:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return None
        elif result.status_code == 100:
            response.status_code = status.HTTP_202_ACCEPTED
            return None
        elif result.status_code == 400:
            response.status_code = status.HTTP_404_NOT_FOUND
            return None
        else:
            return result.result

@router.get("/health")
async def check_health(response: Response) -> HealthCheckStatus:
    async with semaphore:
        output_task = await QueueFSSP.put_task(0, InputTask(
            last_name="Черноглазов",
            first_name="Владислав",
            middle_name="Сергеевич",
            birth_date="22.04.1989"
        ))

        result: Task = await QueueFSSP.get_task(output_task.uuid)
        while result.status_code == 100:
            await asyncio.sleep(1)

            result: Task = await QueueFSSP.get_task(output_task.uuid)
            if result.status_code == 500:
                return HealthCheckStatus(status=False)
            elif result.status_code == 400 or result.status_code == 200:
                return HealthCheckStatus(status=True)
            elif result.status_code == 100:
                continue
            else:
                return HealthCheckStatus(status=False)

        return HealthCheckStatus(status=False)