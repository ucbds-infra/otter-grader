#!/usr/bin/env bash

if [ "${BASE_IMAGE}" != "ucbdsinfra/otter-grader" ]; then
    apt-get clean
    apt-get update
    apt-get install -y pandoc texlive-xetex texlive-fonts-recommended texlive-plain-generic build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev texlive-lang-chinese
    apt-get install -y libnlopt-dev cmake libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev apt-utils libpoppler-cpp-dev libavfilter-dev  libharfbuzz-dev libfribidi-dev imagemagick libmagick++-dev pandoc texlive-xetex texlive-fonts-recommended texlive-plain-generic build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev texlive-lang-chinese libxft-dev

    # install wkhtmltopdf
    wget --quiet -O /tmp/libssl1.1.deb http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1-1ubuntu2.1~18.04.20_amd64.deb
    apt-get install -y /tmp/libssl1.1.deb
    wget --quiet -O /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
    apt-get install -y /tmp/wkhtmltopdf.deb

    # try to set up R
    apt-get clean
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
    add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran40/'

    # install conda
    wget -nv -O {{ autograder_dir }}/source/miniconda_install.sh "{{ miniconda_install_url }}"
    chmod +x {{ autograder_dir }}/source/miniconda_install.sh
    {{ autograder_dir }}/source/miniconda_install.sh -b
    echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc

    export PATH=/root/miniconda3/bin:$PATH
    export TAR="/bin/tar"
fi

# install dependencies with conda
{% if channel_priority_strict %}conda config --set channel_priority strict
{% endif %}conda env create -f {{ autograder_dir }}/source/environment.yml
conda run -n {{ otter_env_name }} Rscript {{ autograder_dir }}/source/requirements.r

# set conda shell
conda init --all

# install ottr; not sure why it needs to happen twice but whatever
git clone --single-branch -b {{ ottr_branch }} https://github.com/ucbds-infra/ottr.git {{ autograder_dir }}/source/ottr
cd {{ autograder_dir }}/source/ottr 
conda run -n {{ otter_env_name }} Rscript -e "devtools::install\\(\\)"
conda run -n {{ otter_env_name }} Rscript -e "devtools::install\\(\\)"
