#!/usr/bin/env bash

set -e

export DEBIAN_FRONTEND=noninteractive
apt-get clean
apt-get update
apt-get install -y wget jq build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libgit2-dev \
    libnlopt-dev cmake libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev \
    apt-utils libpoppler-cpp-dev libavfilter-dev  libharfbuzz-dev libfribidi-dev imagemagick \
    libmagick++-dev libxft-dev

# install mamba
if [ $(uname -p) = "arm" ] || [ $(uname -p) = "aarch64" ] ; \
    then wget -nv https://github.com/conda-forge/miniforge/releases/download/{{ miniforge_version }}/Miniforge3-Linux-aarch64.sh \
        -O {{ autograder_dir }}/source/mamba_install.sh ; \
    else wget -nv https://github.com/conda-forge/miniforge/releases/download/{{ miniforge_version }}/Miniforge3-Linux-x86_64.sh \
        -O {{ autograder_dir }}/source/mamba_install.sh ; \
fi
chmod +x {{ autograder_dir }}/source/mamba_install.sh
{{ autograder_dir }}/source/mamba_install.sh -b
echo "export PATH=/root/miniforge3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniforge3/bin:$PATH
export TAR="/bin/tar"

# install dependencies with mamba{% if channel_priority_strict %}
mamba config set channel_priority strict{% endif %}
mamba env create -f {{ autograder_dir }}/source/environment.yml
mamba install -n {{ otter_env_name }} -c conda-forge nb_conda_kernels
mamba run -n {{ otter_env_name }} bash -c "playwright install-deps && playwright install chromium"{% if has_r_requirements %}
mamba run -n {{ otter_env_name }} Rscript {{ autograder_dir }}/source/requirements.r{% endif %}

# install PDF generation dependencies if enabled
if cat {{ autograder_dir }}/source/otter_config.json | jq -e '[.pdf, .token] | any'; then
    # install pandoc
    wget -nv https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-1-amd64.deb \
        -O /tmp/pandoc.deb
    dpkg -i /tmp/pandoc.deb

    # install tinytex
    mamba install -n {{ otter_env_name }} -c conda-forge r-tinytex
    mamba run -n {{ otter_env_name }} Rscript -e 'tinytex::install_tinytex()'
    echo "export PATH=\$PATH:/root/.TinyTeX/bin/x86_64-linux" >> /root/.bashrc
    export PATH=$PATH:/root/.TinyTeX/bin/x86_64-linux

    # Install dependencies used by nbconvert's default LaTeX template
    tlmgr install adjustbox babel-english background bidi caption \
        cbfonts-fd collectbox enumitem eurosym fancyvrb float fontspec \
        framed grffile hyperref jknapltx ltxcmds mathspec \
        needspace parskip pgf rsfs sectsty soul titling trimspaces \
        ucs ulem unicode-math upquote xcolor xurl zref \
        collection-langchinese collection-langjapanese collection-langkorean  # xeCJK collections 
    # Install fonts for xeCJK
    apt-get install -y fonts-noto-cjk
fi

# set mamba shell
mamba shell init --shell bash
