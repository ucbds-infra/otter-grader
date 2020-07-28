{% if not overwrite %}
# install.packages(c(
#     "git2r",
#     "usethis",
#     "testthat",
#     "devtools",
#     "yaml",
#     "methods",
#     "jsonlite",
#     "knitr"
# ), repos="http://cran.us.r-project.org", dependencies=TRUE)
install.packages(c(
    "usethis",
    "testthat",
    "startup"
), repos="http://cran.us.r-project.org")
{% endif %}{% if other_requirements %}
{{ other_requirements }}
{% endif %}