import base64
import os
import re
import time
import uuid
from typing import Optional

import loguru
import requests
from seleniumwire import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from src.task.schemas import InputTask
from src.utils.get_proxy import get_proxy


class ParserFSSP:
    _url = "https://fssp.gov.ru/iss/ip/?is%5Bvariant%5D=2"
    _current_directory = os.path.dirname(os.path.abspath(__file__))
    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    @classmethod
    def _enter_data(cls, driver, actions, input_task: InputTask):
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "b-form__radio"))
        )
        driver.find_elements(By.CLASS_NAME, "b-form__radio")[0].click()
        loguru.logger.info("Выбираем данные для поиска")

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "chosen-search-input"))
        )
        driver.find_elements(By.CLASS_NAME, "chosen-search-input")[0].click()

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'active-result') and text()='Все регионы']"))
        )
        driver.find_elements(By.XPATH, "//li[contains(@class, 'active-result') and text()='Все регионы']")[0].click()

        href = driver.find_elements(By.XPATH, "//a[contains(@href, 'https://www.gosuslugi.ru/')]")[0]
        actions.move_to_element(href).perform()
        time.sleep(2)

        driver.find_elements(By.XPATH, "//input[contains(@name, 'is[last_name]')]")[0].send_keys(input_task.last_name)

        driver.find_elements(By.XPATH, "//input[contains(@name, 'is[first_name]')]")[0].send_keys(input_task.first_name)

        driver.find_elements(By.XPATH, "//input[contains(@name, 'is[patronymic]')]")[0].send_keys(input_task.middle_name)

        driver.find_elements(By.XPATH, "//input[contains(@name, 'is[date]')]")[0].send_keys(input_task.birth_date)

        loguru.logger.success("Все данные выбрали")

    @classmethod
    def _send_request(cls, driver) -> bool:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'btn-sbm')]"))
        )
        driver.find_elements(By.XPATH, "//input[contains(@id, 'btn-sbm')]")[0].click()

        try:
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "ncapchaAudio"))
            )
            return True
        except:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'b-search-message__text') or contains(@class, 'results')]"))
            )
            if driver.find_element(By.XPATH, "//div[contains(@class, 'b-search-message__text') or contains(@class, 'results')]"):
                text_element = driver.find_element(By.XPATH, "//div[contains(@class, 'b-search-message__text') or contains(@class, 'results')]")
                loguru.logger.warning(text_element.text.strip())
                return False

    @classmethod
    def _get_answer(cls, driver):
        loguru.logger.info("Отправили запрос на получение данных")

        for i in range(0, 5):
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "ncapchaAudio"))
            )
            time.sleep(2)
            driver.find_elements(By.ID, "ncapchaAudio")[0].click()

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//source[contains(@type, 'audio/mpeg')]"))
            )
            audio = driver.find_elements(By.XPATH, "//source[contains(@type, 'audio/mpeg')]")[0].get_attribute("src")

            filename = audio.split("/")[-1]
            response = requests.get(audio, verify=False, headers=cls._headers)
            with open(os.path.join(cls._current_directory, "audio", filename), 'wb') as file:
                file.write(response.content)

            with open(os.path.join(cls._current_directory, "audio", filename), 'rb') as file:
                audio_base64 = base64.b64encode(file.read()).decode('ascii')

            resp = requests.post('http://84.201.178.161:8956/solve/', json={'captcha_base64': audio_base64})
            captcha = resp.json()['captcha_text']
            os.remove(os.path.join(cls._current_directory, "audio", filename))
            loguru.logger.success(f"Каптча распознана - {captcha}")
            driver.find_elements(By.XPATH, "//input[contains(@id, 'captcha-popup-code')]")[0].send_keys(captcha)
            driver.find_elements(By.XPATH, "//input[contains(@id, 'ncapcha-submit')]")[0].click()

            try:
                WebDriverWait(driver, 120).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'b-search-message__text') or contains(@class, 'results-frame') or contains(@class, 'b-form__label--error')]"))
                )

                if len(driver.find_elements(By.CSS_SELECTOR, ".b-form__label--error")) > 0:
                    loguru.logger.warning(driver.find_elements(By.CSS_SELECTOR, ".b-form__label--error")[0].text.strip().lower())
                    continue
                else:
                    break
            except Exception as e:
                break


    @classmethod
    def _get_driver(cls, proxy_string: Optional[str]):
        options = uc.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-web-security')
        proxy = {
            'http': proxy_string,
            'https': proxy_string,
        }

        if proxy_string:
            seleniumwire_options = {
                'proxy': proxy,
            }
            driver = uc.Chrome(headless=False, use_subprocess=False, version_main=133, options=options,
                               seleniumwire_options=seleniumwire_options)
        else:
            driver = uc.Chrome(headless=False, use_subprocess=False, version_main=133, options=options)

        return driver

    @classmethod
    def _get_result(cls, driver):
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'b-search-message__text') or contains(@class, 'results-frame')]"))
        )
        text_element = driver.find_element(By.XPATH, "//div[contains(@class, 'b-search-message__text') or contains(@class, 'results-frame')]").text.strip().lower()

        if "по вашему запросу ничего не найдено" in text_element:
            return True, "Ничего не найдено"
        else:
            results = {}
            rows = driver.find_elements(By.XPATH, '//table//tr[@class!="region-title"]')
            for i, row in enumerate(rows):
                columns = [c.text.strip() for c in row.find_elements(By.XPATH, './/td')]

                person = columns[0].replace('\n', ' ').strip()
                person_lines = columns[0].split('\n')
                ip_num_lines = columns[1].split('\n')
                requisites = columns[2].replace('\n', ' ')
                ip_end = columns[3].replace('\n', ' ')
                amount = columns[5].replace('\n', ' ')
                department = columns[6].replace('\n', ' ')
                bailiff = columns[7].replace('\n', ' ')
                amount_sum_search = re.search(r'\d+\.\d{2}', amount)

                result = {
                    "Должник": person,
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

                results[i] = result
            return True, results

    @classmethod
    def start_parse(cls, input_task: InputTask):
        # proxy_string = await get_proxy()
        driver = cls._get_driver(None)
        loguru.logger.info(f"Старт работы парсера - {input_task}")
        try:
            actions = ActionChains(driver)
            driver.get(cls._url)

            cls._enter_data(driver, actions, input_task)

            count = 1
            while not cls._send_request(driver):
                if count >= 5:
                    raise Exception("Запрос не отправляется. Попробуйте позже")
                driver.execute_script("location.reload();")
                time.sleep(5)
                cls._enter_data(driver, actions, input_task)
                count += 1

            cls._get_answer(driver)

            status, result = cls._get_result(driver)
            loguru.logger.success(result)
            return result
        except Exception as e:
            loguru.logger.exception(e)
            driver.save_screenshot(f"{str(uuid.uuid4())}.png")
        finally:
            time.sleep(1)
            driver.quit()
            time.sleep(1)


if __name__ == '__main__':
    ParserFSSP.start_parse(
        InputTask(
            last_name="Черноглазов",
            first_name="Владислав",
            middle_name="Сергеевич",
            birth_date="22.04.1989"
        )
    )


