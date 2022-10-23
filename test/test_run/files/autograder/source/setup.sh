#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive
apt-get clean
apt-get update
apt-get install -y wget pandoc texlive-xetex texlive-fonts-recommended texlive-plain-generic \
    build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev texlive-lang-chinese

# install conda
if [ $(uname -p) = "arm" ] || [ $(uname -p) = "aarch64" ] ; \
    then wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh \
        -O test/test_generate/test-run-autograder/autograder/source/miniconda_install.sh ; \
    else wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O test/test_generate/test-run-autograder/autograder/source/miniconda_install.sh ; \
fi
chmod +x test/test_generate/test-run-autograder/autograder/source/miniconda_install.sh
test/test_generate/test-run-autograder/autograder/source/miniconda_install.sh -b
echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniconda3/bin:$PATH
export TAR="/bin/tar"

# install dependencies with conda
conda env create -f test/test_generate/test-run-autograder/autograder/source/environment.yml

# set conda shell
conda init --all
