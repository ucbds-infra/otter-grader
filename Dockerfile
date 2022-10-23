FROM ubuntu:22.04
RUN apt-get update && apt-get upgrade -y && apt-get install -y wget
RUN wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    -O /tmp/miniconda_install.sh && \
    chmod +x /tmp/miniconda_install.sh && \
    /tmp/miniconda_install.sh -b && \
    echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc
ENV PATH=/root/miniconda3/bin:$PATH
COPY environment.yml requirements.txt requirements-export.txt requirements-test.txt /tmp/
RUN mkdir -p /tmp/docs
COPY docs/requirements.txt /tmp/docs/
RUN conda env create -f /tmp/environment.yml
ADD . /root/otter-grader
RUN conda init --all
