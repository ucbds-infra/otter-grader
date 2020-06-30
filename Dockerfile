FROM python:3.7
ADD requirements.txt /home/otter-grader-requirements.txt
RUN pip3 install -r /home/otter-grader-requirements.txt
RUN apt-get clean
RUN apt-get update
RUN apt-get install nano -y
RUN apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 \
       libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 \
       libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 \
       libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \
       libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation \
       libappindicator1 libnss3 lsb-release xdg-utils wget
RUN pip3 install git+https://github.com/ucbds-infra/otter-grader.git@08dc6ddfde026fa81cfce93cc1c9a499945f2d11
