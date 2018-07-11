FROM python:2-alpine

RUN mkdir ./app
COPY requirements.txt ./app

WORKDIR ./app


RUN apk update
RUN apk add docker musl-dev linux-headers gcc

RUN pip install -r requirements.txt

COPY . ./app

EXPOSE 2375

CMD [ "python", "./app/Whaler.py" ]

