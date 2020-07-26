#!/usr/bin/env bash

apt-get install -y python3.7 python3-pip python3.7-dev

# apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 \\
#        libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 \\
#        libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 \\
#        libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \\
#        libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation \\
#        libappindicator1 libnss3 lsb-release xdg-utils wget

apt-get update
apt-get install -y pandoc
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-generic-recommended

update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

wget -O /autograder/source/miniconda_install.sh "{{ miniconda_install_url }}"
chmod +x /autograder/source/miniconda_install.sh
/autograder/source/miniconda_install.sh -b
printf "\nexport PATH=/root/miniconda3/bin:$PATH\n" >> /root/.bashrc
source /root/.bashrc

pip3 install -r /autograder/source/requirements.txt
