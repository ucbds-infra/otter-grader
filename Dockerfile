FROM ubuntu:22.04
RUN apt-get update && apt-get upgrade -y && apt-get install -y wget
RUN wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    -O /tmp/miniconda_install.sh && \
    chmod +x /tmp/miniconda_install.sh && \
    /tmp/miniconda_install.sh -b && \
    echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc
ENV PATH=/root/miniconda3/bin:$PATH
ADD . /root/otter-grader
WORKDIR /root/otter-grader
RUN mkdir -p docs
RUN touch docs/requirements.txt
RUN conda env create -f environment.yml
RUN conda init --all
