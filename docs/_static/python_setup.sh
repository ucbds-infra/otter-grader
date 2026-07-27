#!/usr/bin/env bash

set -e

export DEBIAN_FRONTEND=noninteractive
apt-get clean
apt-get update
apt-get install -y wget jq build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev

# install PDF generation dependencies if enabled
if cat /autograder/source/otter_config.json | jq -e '[.pdf, .token] | any'; then
    # install latex
    apt-get install -y texlive-xetex texlive-fonts-recommended texlive-plain-generic texlive-lang-chinese

    # install pandoc
    wget -nv https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-1-amd64.deb \
        -O /tmp/pandoc.deb
    dpkg -i /tmp/pandoc.deb
fi

# install mamba
if [ $(uname -p) = "arm" ] || [ $(uname -p) = "aarch64" ] ; \
    then wget -nv https://github.com/conda-forge/miniforge/releases/download//Miniforge3-Linux-aarch64.sh \
        -O /autograder/source/mamba_install.sh ; \
    else wget -nv https://github.com/conda-forge/miniforge/releases/download//Miniforge3-Linux-x86_64.sh \
        -O /autograder/source/mamba_install.sh ; \
fi
chmod +x /autograder/source/mamba_install.sh
/autograder/source/mamba_install.sh -b
echo "export PATH=/root/miniforge3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniforge3/bin:$PATH
export TAR="/bin/tar"

# install dependencies with mamba
mamba env create -f /autograder/source/environment.yml
mamba install -n otter-env -c conda-forge nb_conda_kernels
mamba run -n otter-env bash -c "playwright install-deps && playwright install chromium"

# set mamba shell
mamba shell init --shell bash