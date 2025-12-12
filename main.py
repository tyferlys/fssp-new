from src.rabbitmq_manager.rabbitmq_manager import RabbitMQManager
from src.services.worker import create_task

if __name__ == "__main__":
    manager = RabbitMQManager(
        count_workers=5,
        callback_function=create_task
    )
    manager.start()