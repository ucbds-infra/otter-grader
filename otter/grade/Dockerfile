ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y curl unzip dos2unix wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/tmp/*

RUN mkdir -p /autograder/source && \
    mkdir -p /autograder/submission && \
    mkdir -p /autograder/results

ADD run_autograder /autograder/run_autograder
ADD setup.sh environment.yml requirements.* /autograder/source/

RUN dos2unix /autograder/run_autograder /autograder/source/setup.sh && \
    chmod +x /autograder/run_autograder && \
    apt-get update && bash /autograder/source/setup.sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# create an empty submission_metadata.json file so that plugins don't error when trying to read it
RUN touch /autograder/submission_metadata.json

ADD otter_config.json run_otter.py /autograder/source/
ADD files* /autograder/source/files/
ADD tests /autograder/source/tests/
