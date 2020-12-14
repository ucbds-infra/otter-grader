#!/usr/bin/env bash

# apt-get clean
# apt-get update
# apt-get install -y python3.7 python3-pip python3.7-dev

apt-get clean
apt-get update
apt-get install -y pandoc
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-generic-recommended

# install wkhtmltopdf
wget --quiet -O /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
apt-get install -y /tmp/wkhtmltopdf.deb

# update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

apt-get clean
apt-get update
apt-get install -y build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libcurl4-openssl-dev libgit2-dev

# install conda
wget -nv -O {{ autograder_dir }}/source/miniconda_install.sh "{{ miniconda_install_url }}"
chmod +x {{ autograder_dir }}/source/miniconda_install.sh
{{ autograder_dir }}/source/miniconda_install.sh -b
echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniconda3/bin:$PATH
export TAR="/bin/tar"

# # install R dependencies
# conda install --yes r-base r-essentials 
# conda install --yes r-devtools -c conda-forge

# # install requirements
# pip3 install -r {{ autograder_dir }}/source/requirements.txt
# pip install -r {{ autograder_dir }}/source/requirements.txt
# Rscript {{ autograder_dir }}/source/requirements.r

# install dependencies with conda
conda env create -f {{ autograder_dir }}/source/environment.yml
conda run -n {{ otter_env_name }} Rscript {{ autograder_dir }}/source/requirements.r

# set conda shell
conda init --all

# install ottr; not sure why it needs to happen twice but whatever
git clone --single-branch -b {{ ottr_branch }} https://github.com/ucbds-infra/ottr.git {{ autograder_dir }}/source/ottr
cd {{ autograder_dir }}/source/ottr 
conda run -n {{ otter_env_name }} Rscript -e "devtools::install\\(\\)"
conda run -n {{ otter_env_name }} Rscript -e "devtools::install\\(\\)"
