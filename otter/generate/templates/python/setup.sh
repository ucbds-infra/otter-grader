#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive
apt-get clean
apt-get update
apt-get install -y wget texlive-xetex texlive-fonts-recommended texlive-plain-generic \
    build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev texlive-lang-chinese

# install pandoc
wget -nv https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-1-amd64.deb \
    -O /tmp/pandoc.deb
dpkg -i /tmp/pandoc.deb

# install mamba
if [ $(uname -p) = "arm" ] || [ $(uname -p) = "aarch64" ] ; \
    then wget -nv https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh \
        -O {{ autograder_dir }}/source/mamba_install.sh ; \
    else wget -nv https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh \
        -O {{ autograder_dir }}/source/mamba_install.sh ; \
fi
chmod +x {{ autograder_dir }}/source/mamba_install.sh
{{ autograder_dir }}/source/mamba_install.sh -b
echo "export PATH=/root/miniforge3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniforge3/bin:$PATH
export TAR="/bin/tar"

# install dependencies with mamba
mamba env create -f {{ autograder_dir }}/source/environment.yml
mamba run -n {{ otter_env_name }} playwright install chromium

# set mamba shell
mamba init --all
