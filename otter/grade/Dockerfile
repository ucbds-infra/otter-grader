ARG BASE_IMAGE=ucbdsinfra/otter-grader
FROM ${BASE_IMAGE}
RUN apt-get update && apt-get install -y curl unzip dos2unix && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN mkdir -p /autograder/source
ARG ZIPPATH
ADD ${ZIPPATH} /tmp/autograder.zip
RUN unzip -d /autograder/source /tmp/autograder.zip && \
    cp /autograder/source/run_autograder /autograder/run_autograder && \
    dos2unix /autograder/run_autograder /autograder/source/setup.sh && \
    chmod +x /autograder/run_autograder && \
    apt-get update && bash /autograder/source/setup.sh && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    mkdir -p /autograder/submission && \
    mkdir -p /autograder/results
