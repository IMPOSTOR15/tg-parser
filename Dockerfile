FROM python:3.9-bullseye
RUN mkdir searchbot
WORKDIR /searchbot/

COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .
CMD python -u /searchbot/main.py