FROM python:3.10-slim

WORKDIR /api

COPY . /api/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE ${API_PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${API_PORT}