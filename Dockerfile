FROM selenium/standalone-chrome:latest

USER root
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN ls -l /app/
ENV SE_OFFLINE=false
CMD ["python3", "main.py"]