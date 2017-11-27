FROM ubuntu:16.04
MAINTAINER ljz@xiaogu-tech.com

RUN apt-get update \
    && apt-get install -y nginx git python3 python3-pip ssh tzdata zip\
    && apt-get clean

RUN locale-gen en_US en_US.UTF-8
ENV LC_ALL="en_US.UTF-8"
RUN echo America/Los_Angeles | tee /etc/timezone && dpkg-reconfigure --frontend noninteractive tzdata

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN pip install --upgrade pip
RUN pip install requests

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

RUN mkdir -p /simulator
COPY ./ /simulator
WORKDIR /simulator

RUN pwd
RUN ls -l
EXPOSE 6666
ENTRYPOINT ["python", "main.py"]
