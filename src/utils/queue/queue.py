import asyncio
import json
import os.path
import uuid
from asyncio import Semaphore
from asyncio import Queue
import datetime
from concurrent.futures.process import ProcessPoolExecutor

import loguru

from src.utils.queue.schemas import State, Task
from src.task.schemas import InputTask, OutputTask
from src.utils.parser.parser_fssp import ParserFSSP


class QueueFSSP:
    state: State = State(started = False, tasks = [])
    semaphore: Semaphore = Semaphore(1)

    @classmethod
    async def put_task(cls, priority_task: int, task_input: InputTask) -> OutputTask:
        async with cls.semaphore:
            if not cls.state.started:
                cls.state.started = True
                asyncio.create_task(cls.start_worker())

            uuid_task = uuid.uuid4().__str__()
            cls.state.tasks.append(
                Task(
                    uuid=uuid_task,
                    priority=priority_task,
                    status_code=100,
                    task_data=task_input
                )
            )

        return OutputTask(uuid=uuid_task)

    @classmethod
    async def get_task(cls, uuid: str) -> Task:
        async with cls.semaphore:
            if not cls.state.started:
                cls.state.started = True
                asyncio.create_task(cls.start_worker())

            for task in cls.state.tasks:
                if task.uuid == uuid:
                    return task
            return None

    @classmethod
    async def start_worker(cls):
        while True:
            task: Task = min(
                (task for task in cls.state.tasks if task.datetime_ready is None),
                key=lambda task: task.priority,
                default=None,
            )

            if task:
                try:
                    result = await asyncio.to_thread(ParserFSSP.start_parse, task.task_data)
                    task.result = result

                    if task.result is None or task.result == "" or task.result == "Ничего не найдено":
                        task.status_code = 400
                    else:
                        task.status_code = 200
                except Exception as e:
                    task.result = ""
                    task.status_code = 500
                finally:
                    task.datetime_ready = datetime.datetime.now()

                cls.state.tasks = list(filter(
                    lambda task: (
                                     task.datetime_ready is not None and
                                     task.datetime_ready + datetime.timedelta(minutes=5) > datetime.datetime.now()
                                 ) or task.datetime_ready is None,
                    cls.state.tasks
                ))
                await asyncio.sleep(3)

            await asyncio.sleep(2)



async def test():
    pass
    # uuid = await QueueInnFns.put_task(
    #     100,
    #     TaskInput(
    #         lastname="test",
    #         firstname="test",
    #         surname="test",
    #         birth_date="test",
    #         passport="test",
    #     )
    # )
    # result = await QueueInnFns.get_task(uuid)
    # print(result)


if __name__ == '__main__':
    asyncio.run(test())

