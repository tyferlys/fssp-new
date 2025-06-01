FROM selenium/standalone-chrome:latest

USER root
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python3", "main.py"]