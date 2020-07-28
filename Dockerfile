# Dockerfile forked from https://github.com/jeffheaton/docker-jupyter-python-r/blob/master/Dockerfile
FROM ubuntu:20.10

# common packages
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y tzdata software-properties-common git vim wget libssl-dev nano && \
    rm -rf /var/lib/apt/lists/*

# miniconda
RUN echo 'export PATH=/opt/conda/bin:$PATH' >> /root/.bashrc && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    rm -rf /var/lib/apt/lists/*

ENV PATH /opt/conda/bin:$PATH

# R pre-reqs
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends fonts-dejavu gfortran \
    gcc && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# R
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y r-base && \
    conda install -c r r-irkernel r-essentials -c conda-forge && \
    rm -rf /var/lib/apt/lists/*

# chromium for nb2pdf
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y chromium-browser

# pandoc and xetex for otter export
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y pandoc && \
    apt-get install -y texlive-xetex texlive-fonts-recommended

# Postgres
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y postgresql postgresql-client libpq-dev

# Python requirements
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN pip install git+https://github.com/ucbds-infra/otter-grader.git@84b05464a4936fa9af3e5bd714ab11be6c8ba560
