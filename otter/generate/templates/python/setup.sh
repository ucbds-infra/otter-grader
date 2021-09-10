#!/usr/bin/env bash

if [ "${BASE_IMAGE}" != "ucbdsinfra/otter-grader" ]; then
    apt-get clean
    apt-get update
    apt-get install -y pandoc texlive-xetex texlive-fonts-recommended texlive-generic-recommended build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev

    # install wkhtmltopdf
    wget --quiet -O /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
    apt-get install -y /tmp/wkhtmltopdf.deb

    # install fandol font for xeCJK
    wget -nv -O /tmp/fandol.zip https://mirrors.ctan.org/fonts/fandol.zip
    unzip -d /tmp/fandol /tmp/fandol.zip
    mkdir -p /usr/share/texlive/texmf-dist/fonts/opentype/public/fandol
    cp /tmp/fandol/fandol/*.otf /usr/share/texlive/texmf-dist/fonts/opentype/public/fandol
    mktexlsr
    fc-cache

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
