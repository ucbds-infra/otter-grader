OS := $(shell uname -s)

docker-test:
	cp -r Dockerfile test-Dockerfile
	printf "\nADD . /home/otter-grader\nRUN pip install /home/otter-grader" >> test-Dockerfile
	docker build . -t otter-test -f test-Dockerfile
	rm test-Dockerfile

documentation:
	sphinx-build -b html docs docs/_build -aEv

tutorial:
	cd docs/tutorial; \
	zip -r tutorial.zip submissions demo.ipynb meta.json requirements.txt -x "*.DS_Store"; \
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


