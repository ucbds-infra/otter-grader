# distro:
# 	rm dist/* || :
# 	python3 update_versions.py
# 	python3 setup.py sdist bdist_wheel

# git-distro:
# 	python3 update_versions.py --git

# pypi:
# 	rm dist/* || :
# 	python3 update_versions.py
# 	python3 setup.py sdist bdist_wheel
# 	python3 -m twine upload dist/*

# test-pypi:
# 	rm dist/* || :
# 	python3 update_versions.py
# 	python3 setup.py sdist bdist_wheel
# 	python3 -m twine upload dist/* --repository-url https://test.pypi.org/legacy/

# docker:
# 	docker build . -t ucbdsinfra/otter-grader
# 	docker push ucbdsinfra/otter-grader

docker-test:
	cp -r Dockerfile test-Dockerfile
	printf "\nADD . /tmp/otter-grader\nRUN pip install /tmp/otter-grader" >> test-Dockerfile
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

docker-grade-test:
	# cp otter/grade/Dockerfile otter/grade/old-Dockerfile
	# printf "\nADD . /tmp/otter-grader\nRUN pip install /tmp/otter-grader" >> otter/grade/Dockerfile
	cp otter/generate/templates/setup.sh otter/generate/templates/old-setup.sh
	printf "\nconda run -n otter-gradescope-env pip install /home/otter-grader" >> otter/generate/templates/setup.sh

cleanup-docker-grade-test:
	# rm otter/grade/Dockerfile
	# mv otter/grade/old-Dockerfile otter/grade/Dockerfile
	rm otter/generate/templates/setup.sh
	mv otter/generate/templates/old-setup.sh otter/generate/templates/setup.sh
