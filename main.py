from src.rabbitmq_manager.rabbitmq_manager import RabbitMQManager
from src.services.worker import ParserFSSP

if __name__ == "__main__":
    manager = RabbitMQManager(
        count_workers=1,
        callback_function=ParserFSSP.create_task
    )
    manager.start()