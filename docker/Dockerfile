FROM python:3.6
RUN wget https://github.com/jgm/pandoc/releases/download/2.0.6/pandoc-2.0.6-1-amd64.deb
RUN dpkg -i pandoc-2.0.6-1-amd64.deb
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
       nb2pdf==0.0.2 \
       otter-grader==0.0.19
RUN apt-get install nano -y