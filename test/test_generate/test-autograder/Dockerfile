FROM gradescope/auto-builds
RUN apt-get update && apt-get install -y curl unzip dos2unix && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN mkdir -p /autograder/source
ADD autograder.zip /tmp/autograder.zip
RUN unzip -d /autograder/source /tmp/autograder.zip
RUN cp /autograder/source/run_autograder /autograder/run_autograder
RUN dos2unix /autograder/run_autograder /autograder/source/setup.sh
RUN chmod +x /autograder/run_autograder
RUN apt-get update && bash /autograder/source/setup.sh && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN mkdir -p /autograder/submission
ADD fails2and6H.ipynb /autograder/submission/fails2and6H.ipynb
RUN mkdir -p /autograder/results
COPY --from=otter-test /tmp/otter-grader /tmp/otter-grader
RUN pip3 install /tmp/otter-grader