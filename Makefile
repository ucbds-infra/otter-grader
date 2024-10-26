PYTEST           = pytest
TESTPATH         = test
PYTESTOPTS       =
COVERAGE         = coverage
DOCKER           = true
SLOW             = true
CLEANUP          = true
ISORT            = isort
ISORTOPTS        =
BLACK            = black
BLACKOPTS        =
CI               = false

_PYTESTOPTS      := -vv --durations=0 --html=pytest-report.html --self-contained-html
_ISORTOPTS       :=
_BLACKOPTS       :=

ifeq ($(DOCKER), false)
	_PYTESTOPTS := $(_PYTESTOPTS) -m "not docker"
endif

ifeq ($(SLOW), false)
	_PYTESTOPTS := $(_PYTESTOPTS) -m "not slow"
endif

ifeq ($(CLEANUP), false)
	_PYTESTOPTS := $(_PYTESTOPTS) --nocleanup
endif

ifeq ($(CI), true)
	_ISORTOPTS := --check --diff
	_BLACKOPTS := --check --diff
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

format:
	$(ISORT) $(_ISORTOPTS) $(ISORTOPTS) .
	$(BLACK) $(_BLACKOPTS) $(BLACKOPTS) .
