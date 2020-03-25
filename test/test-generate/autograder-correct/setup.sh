#!/usr/bin/env bash

apt-get install -y python3.7 python3-pip

update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

pip3 install -r /autograder/source/requirements.txt
