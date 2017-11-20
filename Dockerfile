FROM ubuntu:16.04
MAINTAINER ljz@xiaogu-tech.com

RUN apt-get update \
    && apt-get install -y python3 python3-pip
ENV LC_ALL="en_US.UTF-8"
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN pip install --upgrade pip
RUN pip install requests

COPY ./ /simulator
WORKDIR /simulator


ARG RTA_URL
ENV RTA_URL=${RTA_URL}
ARG RTA_FILE
ENV RTA_FILE=${RTA_FILE}
ARG RTA_RESULT
ENV RTA_RESULT=${RTA_RESULT}
ARG RTA_TAG_KEYS
ENV RTA_TAG_KEYS=${RTA_TAG_KEYS}
ARG RTA_TAG_VALUES
ENV RTA_TAG_VALUES=${RTA_TAG_VALUES}
ARG RTA_FIELD_KEYS
ENV RTA_FIELD_KEYS=${RTA_FIELD_KEYS}
ARG RTA_FIELD_VALUES
ENV RTA_FIELD_VALUES=${RTA_FIELD_VALUES}

ENTRYPOINT ["python", "main.py"]