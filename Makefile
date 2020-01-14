dist:
	rm dist/*
	python3 update_versions.py
	python3 setup.py sdist bdist_wheel

upload:
	rm dist/*
	python3 update_versions.py
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*

test-upload:
	rm dist/*
	python3 update_versions.py
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/* --repository-url https://test.pypi.org/legacy/