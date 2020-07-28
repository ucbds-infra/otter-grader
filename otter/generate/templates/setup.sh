#!/usr/bin/env bash

apt-get clean
apt-get update
apt-get install -y python3.7 python3-pip python3.7-dev

# apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 \\
#        libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 \\
#        libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 \\
#        libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \\
#        libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation \\
#        libappindicator1 libnss3 lsb-release xdg-utils wget

apt-get clean
apt-get update
apt-get install -y pandoc
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-generic-recommended

update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

apt-get clean
apt-get update
apt-get install -y install build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libcurl4-openssl-dev

wget -nv -O {{ autograder_dir }}/source/miniconda_install.sh "{{ miniconda_install_url }}"
chmod +x {{ autograder_dir }}/source/miniconda_install.sh
{{ autograder_dir }}/source/miniconda_install.sh -b
# printf "\nexport PATH=/root/miniconda3/bin:\$PATH\n" >> /root/.bashrc
# source /root/.bashrc
export PATH=/root/miniconda3/bin:$PATH
export TAR="/bin/tar"

conda install --yes r-base r-essentials 
conda install --yes r-devtools -c conda-forge

pip3 install -r {{ autograder_dir }}/source/requirements.txt
Rscript {{ autograder_dir }}/source/requirements.r
# Rscript -e "devtools::install_github('ucbds-infra/ottr')"
git clone --single-branch -b {{ ottr_branch }} https://github.com/ucbds-infra/ottr.git {{ autograder_dir }}/source/ottr
# cd {{ autograder_dir }}/source/ottr 
# Rscript -e "startup::restart()"
# Rscript -e "devtools::install()"
