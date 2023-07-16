# Docker image for setting up a development environment and Otter's automated tests.

FROM docker/buildx-bin as buildx

FROM ubuntu:latest

# Make docker buildx available in the container
COPY --from=buildx /buildx /usr/libexec/docker/cli-plugins/docker-buildx

# Install apt packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y wget make build-essential

# Install mamba
RUN if [ $(uname -p) = "arm" ] || [ $(uname -p) = "aarch64" ] ; \
        then wget -nv https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-aarch64.sh \
            -O {{ autograder_dir }}/source/mamba_install.sh ; \
        else wget -nv https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh \
            -O {{ autograder_dir }}/source/mamba_install.sh ; \
    fi && \
    chmod +x /tmp/mamba_install.sh && \
    /tmp/mamba_install.sh -b
ENV PATH=/root/mambaforge/bin:$PATH

# Create mamba environment
COPY environment.yml requirements.txt requirements-export.txt requirements-test.txt /tmp/
RUN mkdir -p /tmp/docs && touch /tmp/docs/requirements.txt
RUN mamba env create -f /tmp/environment.yml
RUN mamba run -n otter-grader Rscript -e 'install.packages("ottr", dependencies=TRUE, repos="https://cran.r-project.org")'
ADD . /root/otter-grader
RUN mamba run -n otter-grader pip install /root/otter-grader

# Make script executable
RUN chmod +x /root/otter-grader/bin/run_tests
