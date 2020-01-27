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
	docker build ./docker -t otter-test

documentation:
	sphinx-build -b html docs docs/_build -aEv
