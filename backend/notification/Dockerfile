FROM python:3.10-slim

WORKDIR /notification

COPY . /notification/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE ${NOTIFICATION_PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${NOTIFICATION_PORT}