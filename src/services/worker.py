import asyncio
import json
import os
import re

import loguru
#import requests
from bs4 import BeautifulSoup

from src.schemas.schemas import InputTask
from src.services.utils.CaptchaManager import CaptchaManager

from src.services.utils.get_result_html import get_result_html


class ParserFSSP:
    _url = "https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=2"
    _current_directory = os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def _prepare_test_to_html(cls, text: str) -> str:
        json_str = re.sub(r'^[^(]*\((.*)\)[^)]*$', r'\1', text)
        data = json.loads(json_str)
        return data["data"]

    @classmethod
    async def _get_result(cls, input_task: dict):
        result_html = await get_result_html(input_task)
        soup2 = BeautifulSoup(result_html, 'html.parser')

        if "по вашему запросу ничего не найдено" in soup2.text.lower():
            return {}

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
            person = re.sub(r'\s+', ' ', rows[index_start + 0].get_text(separator='\n').strip())
            person_lines = [re.sub(r'\s+', ' ', line.strip()) for line in rows[index_start + 0].get_text(separator='\n').strip().split('\n')]
            ip_num_lines = [re.sub(r'\s+', ' ', line.strip()) for line in rows[index_start + 1].get_text(separator='\n').strip().split('\n')]
            requisites = re.sub(r'\s+', ' ', rows[index_start + 2].get_text(separator='\n').strip())
            ip_end = re.sub(r'\s+', ' ', rows[index_start + 3].get_text(separator='\n').strip())
            amount = re.sub(r'\s+', ' ', rows[index_start + 5].get_text(separator='\n').strip())
            department = re.sub(r'\s+', ' ', rows[index_start + 6].get_text(separator='\n').strip())
            bailiff = re.sub(r'\s+', ' ', rows[index_start + 7].get_text(separator='\n').strip())
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
    async def create_task(cls, input_task: dict):
        loguru.logger.info(f"Старт работы парсера - {input_task}")
        for i in range(0, 5):
            loguru.logger.info(f"Попытка - {i + 1}")
            try:
                result = await cls._get_result(input_task)
                loguru.logger.success(result)
                return result
            except Exception as e:
                loguru.logger.exception(e)

        raise Exception()


if __name__ == '__main__':
    async def main():
        print(await ParserFSSP.create_task({
            "last_name": "Кириллов",
            "first_name": "Владимир",
            "middle_name": "Ильич",
            "birth_date": "31.05.1956"
        }))

    asyncio.run(main())


