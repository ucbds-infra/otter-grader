{% if not overwrite %}install.packages(c(
    "testthat",
    "devtools",
    "yaml",
    "methods",
    "jsonlite",
    "knitr"
), repos="http://cran.us.r-project.org", dependencies=TRUE)

devtools::install_github(c(
    "ucbds-infra/ottr"
)){% endif %}{% if other_requirements %}
{{ other_requirements }}
{% endif %}