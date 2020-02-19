distro:
	rm dist/*
	python3 update_versions.py
	python3 setup.py sdist bdist_wheel

pypi:
	rm dist/*
	python3 update_versions.py
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*

test-pypi:
	rm dist/*
	python3 update_versions.py
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/* --repository-url https://test.pypi.org/legacy/

docker-image:
	docker build ./docker -t ucbdsinfra/otter-grader
	docker push ucbdsinfra/otter-grader

docker-test:
	cp -r ./docker test-docker
	cp -r ./otter test-docker
	cp setup.py test-docker
	cp README.md test-docker
	cp -r ./bin test-docker
	printf "\nADD . /home/otter-grader\nRUN pip3 install /home/otter-grader" >> ./test-docker/Dockerfile
	docker build ./test-docker -t otter-test
	rm -rf ./test-docker

documentation:
	sphinx-build -b html docs docs/_build -aEv
