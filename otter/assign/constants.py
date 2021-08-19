"""Various constants for Otter Assign"""

import re

from jinja2 import Template
from textwrap import indent


NB_VERSION = 4
BLOCK_QUOTE = "```"
COMMENT_PREFIX = "#"
TEST_HEADERS = ["TEST", "HIDDEN TEST"]
ALLOWED_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
NB_VERSION = 4

MD_RESPONSE_CELL_SOURCE = "_Type your answer here, replacing this text._"

BEGIN_TEST_CONFIG_REGEX = r'"""\s*#\s*BEGIN\s*TEST\s*CONFIG'
END_TEST_CONFIG_REGEX = r'"""\s*#\s*END\s*TEST\s*CONFIG'
TEST_REGEX = rf"(##\s*(hidden\s*)?test\s*##\s*|#\s*(hidden\s*)?test\s*|{BEGIN_TEST_CONFIG_REGEX})"
OTTR_TEST_NAME_REGEX = r'''(?:testthat::)?test_that\(['"]([A-Za-z0-9_]+)['"],'''
MD_SOLUTION_REGEX = r"(<strong>|\*{2})solution:?(<\/strong>|\*{2})"
SEED_REGEX = r"##\s*seed\s*##"
IGNORE_REGEX = r"(##\s*ignore\s*##\s*|#\s*ignore\s*)"

# DON'T change this template or the regex that removes hidden tests will break in the R adapter!
OTTR_TEST_FILE_TEMPLATE = Template("""\
test = list(
  name = "{{ name }}",
  cases = list({% for tc in test_cases %}
    ottr::TestCase$new(
      hidden = {% if tc.hidden %}TRUE{% else %}FALSE{% endif %},
      name = {% if tc.name %}"{{ tc.name }}"{% else %}NA{% endif %},
      points = {{ tc.points }},{% if tc.success_message %}
      success_message = {{ tc.success_message }}{% endif %}{% if tc.failure_message %}
      failure_message = {{ tc.failure_message }}{% endif %}
      code = {
        {{ indent(tc.body, "        ").lstrip() }}{# lstrip so that the first line indent is correct #}
      }
    ){% if not loop.last %},{% endif %}{% endfor %}
  )
)""")
OTTR_TEST_FILE_TEMPLATE.globals['indent'] = indent
