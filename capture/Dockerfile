FROM python:2-alpine

RUN apk add tcpdump

RUN mkdir ./app
COPY wrapper.sh ./app
RUN chmod +x app/wrapper.sh

ENTRYPOINT ["/app/wrapper.sh"]

