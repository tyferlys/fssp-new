import json
import multiprocessing
import threading
import time

import loguru
import requests
from twocaptcha.solver import TwoCaptcha
import twocaptcha

class CaptchaManager:
    @classmethod
    def get_answer_captcha(cls, image_base64):
        try:
            solver = TwoCaptcha('626c4a478c32b7e199d8b9e5b4868f10')
            result = solver.normal(image_base64, numeric=1, lang="ru")
            return result["code"]
        except requests.exceptions.ConnectionError:
            loguru.logger.warning("Ошибка подключения к сервису каптчи, переподключаемся")
            return None
        except twocaptcha.api.NetworkException:
            loguru.logger.warning("Сервис каптчи разорвал соединение, пробуем еще раз")
            return None
        except Exception as e:
            loguru.logger.warning("Неизвестная ошибка при решении каптчи")
            return None

