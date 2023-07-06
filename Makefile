PYTEST           = pytest
TESTPATH         = test
PYTESTOPTS       = -v
COVERAGE         = coverage
DOCKER           = true
SLOW             = true
<<<<<<< HEAD
=======
OS              := $(shell uname -s)
>>>>>>> master

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

tutorial:
	cd docs/tutorial; \
	zip -r tutorial.zip submissions demo.ipynb requirements.txt -x "*.DS_Store"; \
	cp tutorial.zip ../_static; \
	rm tutorial.zip
