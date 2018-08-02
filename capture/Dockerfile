FROM alpine

RUN apk add tcpdump==4.9.2-r3

RUN mkdir ./app
COPY wrapper.sh ./app
RUN chmod +x app/wrapper.sh

ENTRYPOINT ["/app/wrapper.sh"]

