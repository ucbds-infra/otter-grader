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

# install mamba
if [ $(uname -p) = "arm" ] || [ $(uname -p) = "aarch64" ] ; \
    then wget -nv https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-aarch64.sh \
        -O {{ autograder_dir }}/source/mamba_install.sh ; \
    else wget -nv https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh \
        -O {{ autograder_dir }}/source/mamba_install.sh ; \
fi
chmod +x {{ autograder_dir }}/source/mamba_install.sh
{{ autograder_dir }}/source/mamba_install.sh -b
echo "export PATH=/root/mambaforge/bin:\$PATH" >> /root/.bashrc

export PATH=/root/mambaforge/bin:$PATH
export TAR="/bin/tar"

# install dependencies with mamba{% if channel_priority_strict %}
mamba config --set channel_priority strict{% endif %}
mamba env create -f {{ autograder_dir }}/source/environment.yml{% if has_r_requirements %}
mamba run -n {{ otter_env_name }} Rscript {{ autograder_dir }}/source/requirements.r{% endif %}

# set mamba shell
mamba init --all

# install ottr
mamba run -n otter-env Rscript -e 'install.packages("https://cran.r-project.org/package=ottr&version={{ ottr_version }}", dependencies=TRUE, repos=NULL)'
