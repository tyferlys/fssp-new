FROM python:3.12

# Создаем рабочую директорию
RUN mkdir /app
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Обновляем пакеты и устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    xvfb \
    x11vnc \
    chromium=127.* \
    && rm -rf /var/lib/apt/lists/*  # Очистка ненужных файлов после установки

# Скачиваем и устанавливаем нужную версию ChromeDriver
RUN CHROME_DRIVER_VERSION=127.0.0.0 \
    && wget https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/bin/ \
    && rm chromedriver_linux64.zip

# Устанавливаем Python зависимости
RUN pip install -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . .

# Устанавливаем переменные окружения для Chromium и ChromeDriver
ENV CHROMIUM_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Открываем порты для приложения
EXPOSE 8000 5900

# Запуск приложения через xvfb
CMD ["sh", "-c", "pkill Xvfb; xvfb-run -a -s '-screen 0 1024x768x24' python3 main.py"]
