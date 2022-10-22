#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive
apt-get clean
apt-get update
apt-get install -y wget pandoc texlive-xetex texlive-fonts-recommended texlive-plain-generic \
    build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev texlive-lang-chinese
apt-get install -y libnlopt-dev cmake libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev \
    apt-utils libpoppler-cpp-dev libavfilter-dev  libharfbuzz-dev libfribidi-dev imagemagick \
    libmagick++-dev pandoc texlive-xetex texlive-fonts-recommended texlive-plain-generic \
    build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev texlive-lang-chinese \
    libxft-dev

# install conda
if [ $(uname -p) = "arm" ] || [ $(uname -p) = "aarch64" ] ; \
    then wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh \
        -O {{ autograder_dir }}/source/miniconda_install.sh ; \
    else wget -nv https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O {{ autograder_dir }}/source/miniconda_install.sh ; \
fi
chmod +x {{ autograder_dir }}/source/miniconda_install.sh
{{ autograder_dir }}/source/miniconda_install.sh -b
echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniconda3/bin:$PATH
export TAR="/bin/tar"

# install dependencies with conda{% if channel_priority_strict %}
conda config --set channel_priority strict{% endif %}
conda env create -f {{ autograder_dir }}/source/environment.yml{% if has_r_requirements %}
conda run -n {{ otter_env_name }} Rscript {{ autograder_dir }}/source/requirements.r{% endif %}

# set conda shell
conda init --all

# install ottr; not sure why it needs to happen twice but whatever
conda run -n otter-env Rscript -e 'install.packages("https://cran.r-project.org/src/contrib/Archive/ottr/ottr_1.1.5.tar.gz", dependencies=TRUE, repos=NULL)'
