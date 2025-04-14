FROM python:3.10-slim

WORKDIR /auth

COPY . /auth/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y postgresql-client
RUN chmod +x /auth/wait-for-it.sh /auth/start.sh

EXPOSE ${AUTH_PORT}

CMD ["/auth/start.sh"]