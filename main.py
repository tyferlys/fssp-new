import tempfile

import loguru
import uvicorn
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from starlette.middleware.cors import CORSMiddleware

from src.task.router import router as task_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_router)

if __name__ == "__main__":
    loguru.logger.info("драйвер запуск")

    temp_user_data_dir = tempfile.mkdtemp()
    options = Options()
    options.binary_location = "/usr/bin/chromium"  # путь к Chromium внутри контейнера
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir={temp_user_data_dir}")
    driver = webdriver.Chrome(options=options)
    loguru.logger.info("драйвер получен")
    uvicorn.run(app, host="0.0.0.0", port=9004)