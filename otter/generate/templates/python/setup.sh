#!/usr/bin/env bash

if [ "${BASE_IMAGE}" != "ucbdsinfra/otter-grader" ]; then
    apt-get clean
    apt-get update
    apt-get install -y pandoc texlive-xetex texlive-fonts-recommended texlive-plain-generic build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev texlive-lang-chinese

    # install wkhtmltopdf
    wget --quiet -O /tmp/libssl1.1.deb http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1-1ubuntu2.1~18.04.20_amd64.deb
    apt-get install -y /tmp/libssl1.1.deb
    wget --quiet -O /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
    apt-get install -y /tmp/wkhtmltopdf.deb

    # install conda
    wget -nv -O {{ autograder_dir }}/source/miniconda_install.sh "{{ miniconda_install_url }}"
    chmod +x {{ autograder_dir }}/source/miniconda_install.sh
    {{ autograder_dir }}/source/miniconda_install.sh -b
    echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc

    export PATH=/root/miniconda3/bin:$PATH
    export TAR="/bin/tar"
fi

# install dependencies with conda
conda env create -f {{ autograder_dir }}/source/environment.yml

# set conda shell
conda init --all
