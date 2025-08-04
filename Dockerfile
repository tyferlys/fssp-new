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

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 5900

CMD ["sh", "-c", "pkill Xvfb; xvfb-run -a -s '-screen 0 1024x768x24' python3 main.py"]
