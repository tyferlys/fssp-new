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
    ВСЕ запросы идут через requests proxies.
    """

    proxies = None

    if proxy:
        login_pass, ip_port = proxy.split("@")
        login, password = login_pass.split(":")
        ip, port = ip_port.split(":")

        proxy_url = f"http://{login}:{password}@{ip}:{port}"

        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }

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

    # 1. createTask (через прокси)
    r = requests.post(
        "https://api.2captcha.com/createTask",
        json={
            "clientKey": api_key,
            "task": task,
            "softId": 3898,
            "languagePool": "rn"
        },
        proxies=proxies,
        timeout=20
    ).json()

    if r.get("errorId") != 0:
        raise Exception(f"createTask error: {r}")

    task_id = r["taskId"]

    # 2. polling результата (через прокси)
    start = time.time()

    while True:
        time.sleep(poll_interval)

        res = requests.post(
            "https://api.2captcha.com/getTaskResult",
            json={
                "clientKey": api_key,
                "taskId": task_id
            },
            proxies=proxies,
            timeout=20
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
            return solve_image_captcha_2captcha('626c4a478c32b7e199d8b9e5b4868f10', image_base64, "1qVXkxLn:q8FTdQyd@154.194.104.8:64298")
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

