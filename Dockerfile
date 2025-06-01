FROM selenium/standalone-chrome:latest

USER root
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN ls -l /app/
RUN cp /app/chromedriver /usr/local/bin/chromedriver && chmod +x /usr/local/bin/chromedriver
ENV SE_OFFLINE=false
CMD ["python3", "main.py"]