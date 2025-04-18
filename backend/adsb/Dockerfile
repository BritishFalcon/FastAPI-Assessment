FROM python:3.10-slim

WORKDIR /adsb

COPY . /adsb/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD uvicorn main:app --host 0.0.0.0 --port 80