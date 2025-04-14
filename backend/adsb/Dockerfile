FROM python:3.10-slim

WORKDIR /adsb

COPY . /adsb/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE ${ADSB_PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${ADSB_PORT}