import asyncio
import inspect
import json
from inspect import iscoroutine
from multiprocessing import Process
from typing import Callable

import aio_pika
import loguru
from pydantic import BaseModel

from config import get_settings

settings = get_settings()
QUEUE_NAME_INPUT = settings.queue_for_tasks_input
QUEUE_NAME_OUTPUT = settings.queue_for_tasks_output
RABBITMQ_URL = f"amqp://{settings.rabbitmq_login}:{settings.rabbitmq_password}@{settings.rabbitmq_host}/"

class RabbitMQManager:
    def __init__(self, count_workers: int, callback_function: Callable):
        self._count_workers = count_workers
        self._callback_function = callback_function

    async def callback(self, message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body)
            result_job: dict = {
                "status": False,
                "result": {}
            }
            loguru.logger.info(f"Началась работа над задачей - {data} - {message.correlation_id}")

            try:
                result_function = self._callback_function(data)
                if iscoroutine(result_function):
                    result_function = await result_function

                result_job["status"] = True
                result_job["result"] = result_function
            except Exception as e:
                loguru.logger.error(f"Ошибка во время работы - {str(e)}")

            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)

            response_message = aio_pika.Message(
                body=json.dumps(result_job).encode(),
                correlation_id=message.correlation_id
            )
            await channel.default_exchange.publish(
                response_message,
                routing_key=message.reply_to
            )

            await connection.close()
            await channel.close()

            loguru.logger.info(f"Ответ отправлен - {message.correlation_id}")

    async def run_single_consumer(self):
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(QUEUE_NAME_INPUT)

        await queue.consume(self.callback)
        await asyncio.Future()

    def _start_process_consumer(self):
        loguru.logger.info("Страт консьюмера")
        asyncio.run(self.run_single_consumer())

    def start(self):
        loguru.logger.info(f"{RABBITMQ_URL} - {QUEUE_NAME_INPUT} - {QUEUE_NAME_OUTPUT}")
        processes = []
        for _ in range(self._count_workers):
            p = Process(target=self._start_process_consumer)
            p.start()
            processes.append(p)

        for p in processes:
            p.join()