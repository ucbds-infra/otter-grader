ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV PATH=/root/mamba/bin:$PATH
ADD . /tmp/otter-grader
RUN mamba run -n otter-env pip install /tmp/otter-grader
RUN rm -rf /tmp/*
