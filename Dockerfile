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
    x11vnc \
    chromium

RUN CHROMEDRIVER_VERSION=135.0.7049.95 && \
    wget -O /tmp/chromedriver_linux64.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver_linux64.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver_linux64.zip /tmp/chromedriver-linux64

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 5900

CMD ["sh", "-c", "pkill Xvfb; xvfb-run -a -s '-screen 0 1024x768x24' python3 main.py"]
