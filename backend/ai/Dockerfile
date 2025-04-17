FROM python:3.10-slim

WORKDIR /ai

COPY . /ai/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE ${AI_PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${AI_PORT} --lifespan on