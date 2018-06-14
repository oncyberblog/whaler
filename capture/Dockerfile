FROM python:2-alpine

RUN apk update
RUN apk add tcpdump

RUN cp usr/sbin/tcpdump usr/bin/tcpdump

#Run tcpdump
CMD usr/bin/tcpdump -W 5 -C 500 -w /tmp/whaler/capture/capfile -i eth0

