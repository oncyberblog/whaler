FROM python:2-alpine

RUN apk update && apk add docker musl-dev linux-headers gcc

RUN mkdir ./app
COPY requirements.txt ./app

WORKDIR ./app

RUN pip install -r requirements.txt
RUN apk add tcpdump==4.9.2-r1
COPY . ./app

EXPOSE 2375

CMD [ "python", "./app/Whaler.py" ]

