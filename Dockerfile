FROM ubuntu:16.04
MAINTAINER ljz@xiaogu-tech.com

RUN apt-get update \
    && apt-get install -y python3 python3-pip
RUN locale-gen en_US en_US.UTF-8
ENV LC_ALL="en_US.UTF-8"
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN pip install --upgrade pip

RUN pip install requests

ENV RTA_URL=${RTA_URL}
ENV RTA_FILE=${RTA_FILE}
ENV RTA_RESULT=${RTA_RESULT}
ENV RTA_TAG_KEYS=${RTA_TAG_KEYS}
ENV RTA_TAG_VALUES=${RTA_TAG_VALUES}
ENV RTA_FIELD_KEYS=${RTA_FIELD_KEYS}
ENV RTA_FIELD_VALUES=${RTA_FIELD_VALUES}

ENTRYPOINT ["python", "main.py"]