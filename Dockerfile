# Dockerfile forked from https://github.com/jeffheaton/docker-jupyter-python-r/blob/master/Dockerfile
FROM ubuntu:20.04

# common packages
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y tzdata git vim wget libssl-dev nano && \
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
    apt-get install -y --no-install-recommends fonts-dejavu gfortran gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# R
RUN apt-get clean && \
    apt-get update && \
    conda install -y "r-base>=4.0.0" r-essentials && \
    conda install -c r r-irkernel r-essentials r-devtools -c conda-forge && \
    rm -rf /var/lib/apt/lists/*

# install wkhtmltopdf for otter export
RUN apt-get clean && \
    apt-get update && \ 
    apt-get install -y pandoc && \
    apt-get install -y -f texlive-xetex texlive-fonts-recommended texlive-lang-chinese && \
    wget --quiet -O /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb && \
    apt-get install -y /tmp/wkhtmltopdf.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the locale to UTF-8 to ensure that Unicode output is encoded correctly
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# create dir for autograder
RUN mkdir /autograder

# Python requirements
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN pip install otter-grader==4.3.1
RUN Rscript -e "install.packages('ottr', dependencies=TRUE, repos='http://cran.us.r-project.org')"
