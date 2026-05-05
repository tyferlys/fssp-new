import loguru
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
from src.services.utils.CaptchaManager import CaptchaManager

def get_result_html(input_task: dict):
    def browser_first_request(input_task):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            url = "https://is-go.fssp.gov.ru/ajax_search"

            params = {
                "callback": "jQuery37106850208189910238_1777367746595",
                "system": "ip",
                "is[extended]": "1",
                "nocache": "1",
                "is[variant]": "1",
                "is[region_id][0]": "-1",
                "is[last_name]": input_task["last_name"],
                "is[first_name]": input_task["first_name"],
                "is[drtr_name]": "",
                "is[ip_number]": "",
                "is[patronymic]": input_task["middle_name"],
                "is[date]": input_task["birth_date"],
                "is[address]": "",
                "is[id_number]": "",
                "is[id_type][0]": "",
                "is[id_issuer]": "",
                "is[inn]": "",
                "_": "1777367746628"
            }

            full_url = url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

            response = page.goto(full_url, wait_until="networkidle")
            text = response.text()
            json_str = re.search(r"\((.*)\)", text, re.S).group(1)

            data = json.loads(json_str)

            return data["data"]

    def parse_captcha(html):
        soup = BeautifulSoup(html, "html.parser")

        captcha_base64 = soup.find("img")["src"]
        code_id = soup.find("form")["url"].split("code_id=")[1].split("&")[0]

        return captcha_base64, code_id

    def browser_second_request(input_task, code_id, captcha):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            url = "https://is-go.fssp.gov.ru/ajax_search"

            params = {
                "callback": "jQuery37105573464652258195_1763455204114",
                "is[variant]": "1",
                "is[ip_number]": "",
                "is[date]": input_task["birth_date"],
                "is[id_type][0]": "",
                "is[inn]": "(empty)",
                "is[region_id][0]": "-1",
                "is[last_name]": input_task["last_name"],
                "is[drtr_name]": "",
                "is[address]": "",
                "is[id_issuer]": "",
                "is[extended]": "1",
                "nocache": "1",
                "is[id_number]": "",
                "system": "ip",
                "is[first_name]": input_task["first_name"],
                "is[patronymic]": input_task["middle_name"],
                "code_id": code_id,
                "code": captcha,
                "_": "1763455204125"
            }

            full_url = url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

            response = page.goto(full_url, wait_until="networkidle")
            text = response.text()
            json_str = re.search(r"\((.*)\)", text, re.S).group(1)

            data = json.loads(json_str)

            return data["data"]

    html1 = browser_first_request(input_task)

    captcha_base64, code_id = parse_captcha(html1)

    for i in range(0, 3):
        captcha = CaptchaManager.get_answer_captcha(captcha_base64)
        if captcha:
            loguru.logger.success(f"Каптча распознана - {captcha}")
            break
        else:
            raise Exception()

    html2 = browser_second_request(input_task, code_id, captcha)

    return html2
