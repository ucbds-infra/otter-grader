#!/usr/bin/env bash

# apt-get clean
# apt-get update
# apt-get install -y python3.7 python3-pip python3.7-dev

apt-get clean
apt-get update
apt-get install -y pandoc
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-plain-generic

# install wkhtmltopdf
wget --quiet -O /tmp/libssl1.1.deb http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1-1ubuntu2.1~18.04.20_amd64.deb
apt-get install -y /tmp/libssl1.1.deb
wget --quiet -O /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
apt-get install -y /tmp/wkhtmltopdf.deb

# install fandol font for xeCJK
wget -nv -O /tmp/fandol.zip https://mirrors.ctan.org/fonts/fandol.zip
unzip -d /tmp/fandol /tmp/fandol.zip
mkdir -p /usr/share/texlive/texmf-dist/fonts/opentype/public/fandol
cp /tmp/fandol/fandol/*.otf /usr/share/texlive/texmf-dist/fonts/opentype/public/fandol
mktexlsr
fc-cache

apt-get clean
apt-get update
apt-get install -y build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libcurl4-openssl-dev libgit2-dev

# install conda
wget -nv -O /autograder/source/miniconda_install.sh "https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-x86_64.sh"
chmod +x /autograder/source/miniconda_install.sh
/autograder/source/miniconda_install.sh -b
echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniconda3/bin:$PATH
export TAR="/bin/tar"

# install dependencies with conda
conda env create -f /autograder/source/environment.yml

# set conda shell
conda init --all