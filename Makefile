OS := $(shell uname -s)
DOCKER_VERSION := $(shell docker version --format '{{.Server.Version}}' | sed "s/+azure//")

.PHONY: docs
docs:
	$(MAKE) -C docs html

docker-test:
	cp -r Dockerfile test-Dockerfile
	printf "\nADD . /home/otter-grader\nRUN pip install /home/otter-grader" >> test-Dockerfile
	printf "\nRUN cd /tmp && curl -sSL -O https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz && tar zxf docker-${DOCKER_VERSION}.tgz && mv ./docker/docker /usr/local/bin && chmod +x /usr/local/bin/docker && rm -rf /tmp/*" >> test-Dockerfile
	printf "\nCOPY --from=docker/buildx-bin /buildx /usr/libexec/docker/cli-plugins/docker-buildx" >> test-Dockerfile
	printf "\nENV PYTHONUNBUFFERED 1" >> test-Dockerfile
	docker build . -t otter-test -f test-Dockerfile --cache-from ucbdsinfra/otter-grader:latest
	rm test-Dockerfile

docker-ci-test:
	cp -r Dockerfile test-Dockerfile
	printf "\nADD . /home/otter-grader\nRUN pip install /home/otter-grader" >> test-Dockerfile
	printf "\nRUN cd /tmp && curl -sSL -O https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz && tar zxf docker-${DOCKER_VERSION}.tgz && mv ./docker/docker /usr/local/bin && chmod +x /usr/local/bin/docker && rm -rf /tmp/*" >> test-Dockerfile
	printf "\nCOPY --from=docker/buildx-bin /buildx /usr/libexec/docker/cli-plugins/docker-buildx" >> test-Dockerfile
	printf "\nENV PYTHONUNBUFFERED 1" >> test-Dockerfile
	docker buildx build . --load -t otter-test -f test-Dockerfile --cache-from=type=gha --cache-to=type=gha,mode=max
	rm test-Dockerfile

tutorial:
	cd docs/tutorial; \
	zip -r tutorial.zip submissions demo.ipynb requirements.txt -x "*.DS_Store"; \
	cp tutorial.zip ../_static; \
	rm tutorial.zip

docker-grade-test:
ifeq ($(OS), Darwin)
	cp otter/generate/templates/python/setup.sh otter/generate/templates/python/old-setup.sh
	printf "\nconda run -n otter-env pip install /home/otter-grader" >> otter/generate/templates/python/setup.sh
	sed -i '' -e "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/setup.sh
	sed -i '' -e "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/run_autograder
else
	cp otter/generate/templates/python/setup.sh otter/generate/templates/python/old-setup.sh
	printf "\nconda run -n otter-env pip install /home/otter-grader" >> otter/generate/templates/python/setup.sh
	sed -i "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/setup.sh
	sed -i "s+ucbdsinfra/otter-grader+otter-test+" otter/generate/templates/python/run_autograder
endif

cleanup-docker-grade-test:
ifeq ($(OS), Darwin)
	rm otter/generate/templates/python/setup.sh
	mv otter/generate/templates/python/old-setup.sh otter/generate/templates/python/setup.sh
	sed -i '' -e "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/setup.sh
	sed -i '' -e "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/run_autograder
else
	rm otter/generate/templates/python/setup.sh
	mv otter/generate/templates/python/old-setup.sh otter/generate/templates/python/setup.sh
	sed -i "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/setup.sh
	sed -i "s+otter-test+ucbdsinfra/otter-grader+" otter/generate/templates/python/run_autograder
endif
