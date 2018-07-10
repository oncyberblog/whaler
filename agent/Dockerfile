FROM python:2-alpine

RUN mkdir ./app
COPY requirements.txt ./app

WORKDIR ./app

RUN pip install -r requirements.txt

RUN apk update
RUN apk add docker

COPY . ./app

EXPOSE 2375

CMD [ "python", "./app/Whaler.py" ]

