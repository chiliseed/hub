FROM python:3.8.6-slim-buster AS api

LABEL maintainer="Chiliseed LTD"

ARG requirements=requirements/dev.txt
ENV PATH=$PATH:/app
ENV PYTHONPATH=$PYTHONPATH:/app

RUN mkdir /app
RUN mkdir -p ~/.terraform.d/plugins/linux_amd64
WORKDIR /app

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
        unzip \
        gcc \
        libpq-dev \
        postgresql-client \
        wget && \
    pip install -U pip ipython && \
    wget https://releases.hashicorp.com/terraform/0.13.4/terraform_0.13.4_linux_amd64.zip && \
    unzip terraform_0.13.4_linux_amd64.zip -d /usr/local/bin && \
    rm -rf terraform_0.13.4_linux_amd64.zip && \
    wget https://releases.hashicorp.com/terraform-provider-aws/2.70.0/terraform-provider-aws_2.70.0_linux_amd64.zip && \
    unzip terraform-provider-aws_2.70.0_linux_amd64.zip -d ~/.terraform.d/plugins/linux_amd64 && \
    rm -rf terraform-provider-aws_2.70.0_linux_amd64.zip && \
    wget https://releases.hashicorp.com/terraform-provider-null/2.1.2/terraform-provider-null_2.1.2_linux_amd64.zip && \
    unzip terraform-provider-null_2.1.2_linux_amd64.zip -d ~/.terraform.d/plugins/linux_amd64 && \
    rm -rf terraform-provider-null_2.1.2_linux_amd64.zip && \
    wget https://releases.hashicorp.com/terraform-provider-random/2.3.0/terraform-provider-random_2.3.0_linux_amd64.zip && \
    unzip terraform-provider-random_2.3.0_linux_amd64.zip -d ~/.terraform.d/plugins/linux_amd64 && \
    rm -rf terraform-provider-random_2.3.0_linux_amd64.zip && \
    wget https://releases.hashicorp.com/terraform-provider-template/2.1.2/terraform-provider-template_2.1.2_linux_amd64.zip && \
    unzip terraform-provider-template_2.1.2_linux_amd64.zip -d ~/.terraform.d/plugins/linux_amd64 && \
    rm -rf terraform-provider-template_2.1.2_linux_amd64.zip && \
    apt-get clean


COPY requirements requirements

RUN pip install -r ${requirements}

COPY src/ /app

VOLUME ["./src/infra_executors/terraform_plans"]
VOLUME ["./src/infra_executors/exec_logs"]
VOLUME ["./src/infra_executors/key_pairs"]

CMD bash /app/runner.sh


FROM api AS scheduler

CMD bash /app/scheduler_runner.sh
