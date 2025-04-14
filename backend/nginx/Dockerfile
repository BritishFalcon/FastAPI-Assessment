FROM nginx:alpine

RUN apk add --no-cache gettext

COPY nginx.conf /etc/nginx/nginx.conf.template

CMD envsubst '$ADSB_PORT $MAPPING_PORT $AUTH_PORT $API_PORT $APP_PORT' \
  < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && \
  nginx -g 'daemon off;'