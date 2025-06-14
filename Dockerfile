FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev \
    && pip install --no-cache-dir aiogram python-dotenv

WORKDIR /app
COPY . /app

CMD ["python", "bots/BOT_P.py"]
