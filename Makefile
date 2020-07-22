distro:
	rm dist/*
	python3 update_versions.py
	python3 setup.py sdist bdist_wheel

git-distro:
	python3 update_versions.py --git

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

docker:
	docker build . -t ucbdsinfra/otter-grader:beta
	docker push ucbdsinfra/otter-grader:beta

docker-test:
	cp -r Dockerfile test-Dockerfile
	printf "\nADD . /home/otter-grader\nRUN pip3 install /home/otter-grader" >> test-Dockerfile
	docker build . -t otter-test -f test-Dockerfile
	rm test-Dockerfile

documentation:
	# sphinx-apidoc -fo docs otter
	sphinx-build -b html docs docs/_build -aEv

tutorial:
	# rm docs/tutorial/tutorial.zip
	cd docs/tutorial; \
	zip -r tutorial.zip assign generate grade -x "*.DS_Store"; \
	cp tutorial.zip ../_static; \
	rm tutorial.zip
