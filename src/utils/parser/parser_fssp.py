import base64
import os
import time

import loguru
import requests
from seleniumwire import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from src.task.schemas import InputTask


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
    def _get_answer(cls, driver):
        loguru.logger.info("Отправили запрос на получение данных")

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

    @classmethod
    def start_parse(cls, input_task: InputTask):
        options = uc.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-web-security')
        driver = uc.Chrome(headless=False, use_subprocess=False, version_main=131, options=options)
        try:
            actions = ActionChains(driver)

            driver.get(cls._url)

            cls._enter_data(driver, actions, input_task)

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'btn-sbm')]"))
            )
            driver.find_elements(By.XPATH, "//input[contains(@id, 'btn-sbm')]")[0].click()

            cls._get_answer(driver)
        except Exception as e:
            loguru.logger.error(e)
        finally:
            time.sleep(1)
            driver.quit()
            time.sleep(1)


if __name__ == '__main__':
    for i in range(0, 100):
        try:
            ParserFSSP.start_parse(InputTask(
                last_name="Климов",
                first_name="Денис",
                middle_name="Максимович",
                birth_date="18.11.2003"
            ))
        except:
            pass

