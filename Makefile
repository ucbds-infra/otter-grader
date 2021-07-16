.PHONY: docs
docs:
	$(MAKE) -C docs html

docker-test:
	cp -r Dockerfile test-Dockerfile
	printf "\nADD . /home/otter-grader\nRUN pip install /home/otter-grader" >> test-Dockerfile
	docker build . -t otter-test -f test-Dockerfile
	rm test-Dockerfile

tutorial:
	# rm docs/tutorial/tutorial.zip
	cd docs/tutorial; \
	zip -r tutorial.zip submissions demo.ipynb meta.json requirements.txt -x "*.DS_Store"; \
	cp tutorial.zip ../_static; \
	rm tutorial.zip

docker-grade-test:
	# cp otter/grade/Dockerfile otter/grade/old-Dockerfile
	# printf "\nADD . /home/otter-grader\nRUN pip install /home/otter-grader" >> otter/grade/Dockerfile
	cp otter/generate/templates/python/setup.sh otter/generate/templates/python/old-setup.sh
	printf "\nconda run -n otter-env pip install /home/otter-grader" >> otter/generate/templates/python/setup.sh

cleanup-docker-grade-test:
	# rm otter/grade/Dockerfile
	# mv otter/grade/old-Dockerfile otter/grade/Dockerfile
	rm otter/generate/templates/python/setup.sh
	mv otter/generate/templates/python/old-setup.sh otter/generate/templates/python/setup.sh
