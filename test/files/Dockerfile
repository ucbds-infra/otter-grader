ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV PATH=/root/miniconda3/bin:$PATH
ADD . /tmp/otter-grader
RUN conda run -n otter-env pip install /tmp/otter-grader
RUN rm -rf /tmp/*
