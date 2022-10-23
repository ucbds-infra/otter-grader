FROM ubuntu:22.04
RUN apt-get update && apt-get upgrade -y && apt-get install -y wget make
RUN wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    -O /tmp/miniconda_install.sh && \
    chmod +x /tmp/miniconda_install.sh && \
    /tmp/miniconda_install.sh -b && \
    echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc && \
    echo "source /root/.bashrc" > /root/.bash_profile
ENV PATH=/root/miniconda3/bin:$PATH
COPY environment.yml requirements.txt requirements-export.txt requirements-test.txt /tmp/
RUN mkdir -p /tmp/docs && touch /tmp/docs/requirements.txt
RUN conda env create -f /tmp/environment.yml
ADD . /root/otter-grader
RUN conda run -n otter-grader Rscript -e 'install.packages("ottr", dependencies=TRUE, repos="https://cran.us.r-project.org")'
# RUN conda init --all
WORKDIR /root/otter-grader
RUN chmod +x bin/run_tests
# SHELL ["/bin/bash", "-c"]
# SHELL ["conda", "run", "-n", "otter-grader", "/bin/bash", "-c"]
RUN which -a docker
ENTRYPOINT [ "bin/run_tests" ]
