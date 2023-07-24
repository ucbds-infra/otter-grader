FROM base_image
ENV PATH=/root/mambaforge/bin:$PATH
ADD . /tmp/otter-grader
RUN mamba run -n otter-env pip install /tmp/otter-grader
RUN rm -rf /tmp/*
