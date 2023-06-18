PYTEST           = pytest
TESTPATH         = test
PYTESTOPTS       = -v
COVERAGE         = coverage
DOCKER           = true
SLOW             = true
OS              := $(shell uname -s)

ifeq ($(DOCKER), false)
	PYTESTOPTS := $(PYTESTOPTS) -m "not docker"
endif

ifeq ($(SLOW), false)
	PYTESTOPTS := $(PYTESTOPTS) -m "not slow"
endif

.PHONY: test
test:
	$(PYTEST) $(TESTPATH) $(PYTESTOPTS)

testcov:
	$(COVERAGE) run -m pytest $(TESTPATH) $(PYTESTOPTS)

htmlcov: testcov
	$(COVERAGE) html

.PHONY: docs
docs:
	$(MAKE) -C docs html

docker-test-prepare: 
	cp -r Dockerfile test-Dockerfile
	printf "\nADD . /home/otter-grader\nRUN pip install /home/otter-grader" >> test-Dockerfile
	printf "\nARG DOCKER_VERSION" >> test-Dockerfile
	printf "\nRUN cd /tmp && curl -sSL -O https://download.docker.com/linux/static/stable/x86_64/docker-$$%s.tgz && tar zxf docker-$$%s.tgz && mv ./docker/docker /usr/local/bin && chmod +x /usr/local/bin/docker && rm -rf /tmp/*" "{DOCKER_VERSION}" "{DOCKER_VERSION}" >> test-Dockerfile
	printf "\nCOPY --from=docker/buildx-bin /buildx /usr/libexec/docker/cli-plugins/docker-buildx" >> test-Dockerfile
	printf "\nENV PYTHONUNBUFFERED 1" >> test-Dockerfile

docker-test: docker-test-prepare
	docker build . -t otter-test -f test-Dockerfile --cache-from ucbdsinfra/otter-grader:latest
	rm test-Dockerfile

docker-ci-test-cleanup:
	rm test-Dockerfile

tutorial:
	cd docs/tutorial; \
	zip -r tutorial.zip submissions demo.ipynb requirements.txt -x "*.DS_Store"; \
	cp tutorial.zip ../_static; \
	rm tutorial.zip

docker-grade-test:
	cp otter/generate/templates/python/setup.sh otter/generate/templates/python/old-setup.sh
	printf "\nconda run -n otter-env pip install /home/otter-grader" >> otter/generate/templates/python/setup.sh
ifeq ($(OS), Darwin)
	sed -i '' -e "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/setup.sh
	sed -i '' -e "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/run_autograder
else
	sed -i "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/setup.sh
	sed -i "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/run_autograder
endif

cleanup-docker-grade-test:
	rm otter/generate/templates/python/setup.sh
	mv otter/generate/templates/python/old-setup.sh otter/generate/templates/python/setup.sh
ifeq ($(OS), Darwin)
	sed -i '' -e "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/setup.sh
	sed -i '' -e "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/run_autograder
else
	sed -i "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/setup.sh
	sed -i "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/run_autograder
endif
