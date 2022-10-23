ARG BASE_IMAGE=ubuntu:22.04

FROM ${BASE_IMAGE}

RUN apt-get update && \
    apt-get install -y curl unzip dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/tmp/*

RUN mkdir -p /autograder/source && \
    mkdir -p /autograder/submission && \
    mkdir -p /autograder/results

ENV BASE_IMAGE=$BASE_IMAGE
ADD run_autograder /autograder/run_autograder
ADD setup.sh environment.yml requirements.* /autograder/source/

RUN dos2unix /autograder/run_autograder /autograder/source/setup.sh && \
    chmod +x /autograder/run_autograder && \
    apt-get update && bash /autograder/source/setup.sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ADD otter_config.json run_otter.py /autograder/source/
ADD files* /autograder/source/files/
ADD tests /autograder/source/tests/
