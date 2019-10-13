FROM python:3.7.4-slim-buster

LABEL maintainer="Chiliseed LTD"

ARG requirements=requirements/dev.txt

RUN mkdir /app
WORKDIR /app

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
        gcc \
        libpq-dev \
        postgresql-client \
        wget && \
    apt-get clean && \
    pip install -U pip ipython

COPY requirements requirements

RUN pip install -r ${requirements}

COPY src /app

EXPOSE 8000
