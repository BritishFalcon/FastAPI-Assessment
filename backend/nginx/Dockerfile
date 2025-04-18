FROM nginx:alpine

RUN apk add --no-cache gettext

COPY nginx.conf /etc/nginx/nginx.conf

CMD nginx -g 'daemon off;'