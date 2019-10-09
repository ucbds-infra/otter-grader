FROM python:3.6
RUN wget https://github.com/jgm/pandoc/releases/download/1.15.1/pandoc-1.15.1-1-amd64.deb
RUN dpkg -i pandoc-1.15.1-1-amd64.deb
RUN apt-get update
RUN apt-get clean
RUN apt-get install texlive-xetex -y
RUN pip3 install --no-cache-dir \
       datascience \
       jupyter_client \
       ipykernel \
       matplotlib \
       pandas \
       ipywidgets \
       scipy \
       gofer-grader==1.0.3 \
       nb2pdf==0.0.1 \
       otter-grader==0.0.6