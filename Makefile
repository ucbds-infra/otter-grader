PYTEST           = pytest
TESTPATH         = test
PYTESTOPTS       =
COVERAGE         = coverage
DOCKER           = true
SLOW             = true

_PYTESTOPTS      := -vv --durations=0

ifeq ($(DOCKER), false)
	_PYTESTOPTS := $(_PYTESTOPTS) -m "not docker"
endif

ifeq ($(SLOW), false)
	_PYTESTOPTS := $(_PYTESTOPTS) -m "not slow"
endif

_PYTESTOPTS := $(_PYTESTOPTS) $(PYTESTOPTS)

.PHONY: test
test:
	$(PYTEST) $(TESTPATH) $(_PYTESTOPTS)

testcov:
	$(COVERAGE) run -m pytest $(TESTPATH) $(_PYTESTOPTS)

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
