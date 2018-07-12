FROM python:2-alpine

RUN apk update && apk add docker musl-dev linux-headers gcc

RUN mkdir ./app
COPY requirements.txt ./app

WORKDIR ./app

RUN pip install -r requirements.txt

COPY . ./app

EXPOSE 2375

CMD [ "python", "./app/Whaler.py" ]

