FROM docker/buildx-bin as buildx

FROM ubuntu:latest

# Make docker buildx available in the container
COPY --from=buildx /buildx /usr/libexec/docker/cli-plugins/docker-buildx

# Install apt packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y wget make

# Install conda
RUN wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    -O /tmp/miniconda_install.sh && \
    chmod +x /tmp/miniconda_install.sh && \
    /tmp/miniconda_install.sh -b
ENV PATH=/root/miniconda3/bin:$PATH

# Create conda environment
COPY environment.yml requirements.txt requirements-export.txt requirements-test.txt /tmp/
RUN mkdir -p /tmp/docs && touch /tmp/docs/requirements.txt
RUN conda env create -f /tmp/environment.yml
ADD . /root/otter-grader
RUN conda run -n otter-grader Rscript -e 'install.packages("ottr", dependencies=TRUE, repos="https://cran.us.r-project.org")'

# Make script executable
RUN chmod +x /root/otter-grader/bin/run_tests
