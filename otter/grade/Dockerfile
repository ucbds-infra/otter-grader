ARG BASE_IMAGE=ucbdsinfra/otter-grader
FROM ${BASE_IMAGE}
ARG ZIPPATH
RUN apt-get update && apt-get install -y curl unzip dos2unix && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN mkdir -p /autograder/source
ADD ${ZIPPATH} /tmp/autograder.zip
RUN unzip -d /autograder/source /tmp/autograder.zip
RUN cp /autograder/source/run_autograder /autograder/run_autograder
RUN dos2unix /autograder/run_autograder /autograder/source/setup.sh
RUN chmod +x /autograder/run_autograder
RUN apt-get update && bash /autograder/source/setup.sh && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN mkdir -p /autograder/submission
RUN mkdir -p /autograder/results
