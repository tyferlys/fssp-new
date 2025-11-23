import base64
import json
import os
import re
import shutil
import tempfile
import time
import uuid

import loguru
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from src.task.schemas import InputTask, OutputTask
from src.utils.CaptchaManager import CaptchaManager


class ParserFSSP:
    _url = "https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=2"
    _current_directory = os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def _prepare_test_to_html(cls, text: str) -> str:
        json_str = re.sub(r'^[^(]*\((.*)\)[^)]*$', r'\1', text)
        data = json.loads(json_str)
        return data["data"]

    @classmethod
    def _get_result(cls, input_task: InputTask):
        params1 = {
            "callback": "jQuery37105573464652258195_1763455204114",
            "system": "ip",
            "is[extended]": "1",
            "nocache": "1",
            "is[variant]": "1",
            "is[region_id][0]": "-1",
            "is[last_name]": input_task.last_name,
            "is[first_name]": input_task.first_name,
            "is[drtr_name]": "",
            "is[ip_number]": "",
            "is[patronymic]": input_task.middle_name,
            "is[date]": input_task.birth_date,
            "is[address]": "",
            "is[id_number]": "",
            "is[id_type][0]": "",
            "is[id_issuer]": "",
            "is[inn]": "",
            "_": "1763455204124"
        }
        headers1 = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        response1 = requests.get("https://is-go.fssp.gov.ru/ajax_search", params=params1, headers=headers1)
        soup1 = BeautifulSoup(cls._prepare_test_to_html(response1.text), 'html.parser')

        captcha_base64 = soup1.find('img').get('src')
        code_id = soup1.find('form').get('url').split('code_id=')[1].split('&')[0]

        captcha = CaptchaManager.get_answer_captcha(captcha_base64)
        loguru.logger.success(f"Каптча распознана - {captcha}")

        params2 = {
            "callback": "jQuery37105573464652258195_1763455204114",
            "is[variant]": "1",
            "is[ip_number]": "",
            "is[date]": input_task.birth_date,
            "is[id_type][0]": "",
            "is[inn]": "(empty)",
            "is[region_id][0]": "-1",
            "is[last_name]": input_task.last_name,
            "is[drtr_name]": "",
            "is[address]": "",
            "is[id_issuer]": "",
            "is[extended]": "1",
            "nocache": "1",
            "is[id_number]": "",
            "system": "ip",
            "is[first_name]": input_task.first_name,
            "is[patronymic]": input_task.middle_name,
            "code_id": code_id,
            "code": captcha,
            "_": "1763455204125"
        }
        headers2 = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "cookie": "_ym_uid=1760168378506978246; _ym_d=1760168378; _ym_isad=2",
            "referer": "https://fssp.gov.ru/",
            "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "script",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }

        response2 = requests.get("https://is-go.fssp.gov.ru/ajax_search", params=params2, headers=headers2)
        soup2 = BeautifulSoup(cls._prepare_test_to_html(response2.text), 'html.parser')

        if "по вашему запросу ничего не найдено" in soup2.text.lower():
            return "Ничего не найдено"

        results_frame = soup2.find('div', class_='results-frame')
        if not results_frame:
            raise Exception("Таблица не найдена")

        rows = soup2.find_all('td', attrs={'colspan': False})

        if len(rows) % 8 == 0:
            loguru.logger.success("Количество блоков верное")
        else:
            loguru.logger.warning("Количество блоков неверное")
            raise Exception("Ошибка в количестве блоков")

        results = {}
        index_start = 0
        index_block = 0
        while index_start + 8 <= len(rows):
            person = re.sub(r'\s+', ' ', rows[index_start + 0].text.strip())
            person_lines = [re.sub(r'\s+', ' ', line.strip()) for line in rows[index_start + 0].text.strip().split('\n')]
            ip_num_lines = [re.sub(r'\s+', ' ', line.strip()) for line in rows[index_start + 1].text.strip().split('\n')]
            requisites = re.sub(r'\s+', ' ', rows[index_start + 2].text.strip())
            ip_end = re.sub(r'\s+', ' ', rows[index_start + 3].text.strip())
            amount = re.sub(r'\s+', ' ', rows[index_start + 5].text.strip())
            department = re.sub(r'\s+', ' ', rows[index_start + 6].text.strip())
            bailiff = re.sub(r'\s+', ' ', rows[index_start + 7].text.strip())
            amount_sum_search = re.search(r'\d+\.\d{2}', amount)

            result = {
                "Должник": person.strip(),
                "ФИО": person_lines[0].strip(),
                "Дата рождения": person_lines[1].strip(),
                "Исполнительное производство": re.sub(r' от .+', '', ip_num_lines[0]),
                "Дата начала производства": re.sub(r'.+ от ', '', ip_num_lines[0]),
                "Реквизиты исполнительного документа": requisites,
                "Дата, причина окончания": ip_end,
                "Окончено": ip_end != "",
                "Предмет исполнения, сумма непогашенной задолженности": amount,
                "Отдел судебных приставов": department,
                "Судебный пристав-исполнитель": bailiff
            }

            if amount_sum_search:
                result["Сумма задолженности"] = amount_sum_search.group(0)

            if len(person_lines) > 2:
                result["Место рождения"] = person_lines[2].strip()

            if len(ip_num_lines) > 1:
                result["Свободное исполнительное производство"] = ip_num_lines[1].strip()

            if ip_end:
                ip_date_end = re.search(r'\d{2}\.\d{2}\.\d{4}', ip_end)
                if ip_date_end:
                    result["Дата окончания"] = ip_date_end.group()

                result["Причина окончания"] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', ip_end).strip()

            results[index_block] = result
            index_block += 1
            index_start += 8

        return results

    @classmethod
    def start_parse(cls, input_task: InputTask):
        loguru.logger.info(f"Старт работы парсера - {input_task}")
        for i in range(0, 3):
            loguru.logger.info(f"Попытка - {i + 1}")
            try:
                result = cls._get_result(input_task)
                loguru.logger.success(result)
                return result
            except Exception as e:
                loguru.logger.error(e)

        raise Exception()


if __name__ == '__main__':
    ParserFSSP.start_parse(
        InputTask(
            last_name="Черноглазов",
            first_name="Владислав",
            middle_name="Сергеевич",
            birth_date="22.04.1989"
        )
    )


