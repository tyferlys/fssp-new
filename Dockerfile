FROM python:3.12

RUN mkdir /app
WORKDIR /app

COPY requirements.txt .

RUN apt-get -y update

RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    xvfb \
    x11vnc

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

RUN CHROME_VERSION=137.0.7151.55 && \
    echo "Using Chrome version: $CHROME_VERSION" && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /usr/local/bin/chromedriver-linux64


RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 5900

CMD ["python3", "main.py"]
