import json
import multiprocessing
import threading
import time

import loguru
import requests
from twocaptcha import TwoCaptcha
import twocaptcha

import requests
import time


def solve_image_captcha_2captcha(
    api_key: str,
    image_base64: str,
    proxy: str | None = None,
    timeout: int = 120,
    poll_interval: int = 5
) -> str:
    """
    Решает ImageToText капчу через 2Captcha API v2.

    proxy формат:
    "login:password@ip:port"
    """

    task = {
        "type": "ImageToTextTask",
        "body": image_base64,
        "phrase": False,
        "case": True,
        "numeric": 0,
        "math": False,
        "minLength": 1,
        "maxLength": 5,
    }

    # добавляем прокси если есть
    if proxy:
        login_pass, ip_port = proxy.split("@")
        login, password = login_pass.split(":")
        ip, port = ip_port.split(":")

        task.update({
            "proxyType": "http",
            "proxyAddress": ip,
            "proxyPort": int(port),
            "proxyLogin": login,
            "proxyPassword": password
        })

    # 1. создаём задачу
    r = requests.post(
        "https://api.2captcha.com/createTask",
        json={
            "clientKey": api_key,
            "task": task,
            "softId": 3898,
            "languagePool": "rn"
        }
    ).json()

    if r.get("errorId") != 0:
        raise Exception(f"createTask error: {r}")

    task_id = r["taskId"]

    # 2. ждём результат
    start = time.time()

    while True:
        time.sleep(poll_interval)

        res = requests.post(
            "https://api.2captcha.com/getTaskResult",
            json={
                "clientKey": api_key,
                "taskId": task_id
            }
        ).json()

        if res.get("status") == "ready":
            return res["solution"]["text"]

        if res.get("errorId", 0) != 0:
            raise Exception(f"getTaskResult error: {res}")

        if time.time() - start > timeout:
            raise TimeoutError("Captcha solving timeout")

class CaptchaManager:
    @classmethod
    def get_answer_captcha(cls, image_base64):
        try:
            return solve_image_captcha_2captcha('626c4a478c32b7e199d8b9e5b4868f10', image_base64, "1qVXkxLn:q8FTdQyd@141.133.105.235:63578")
        except requests.exceptions.ConnectionError:
            loguru.logger.warning("Ошибка подключения к сервису каптчи, переподключаемся")
            return None
        except twocaptcha.api.NetworkException as e:
            loguru.logger.exception(e)
            loguru.logger.warning("Сервис каптчи разорвал соединение, пробуем еще раз")
            return None
        except Exception as e:
            loguru.logger.warning("Неизвестная ошибка при решении каптчи")
            return None

