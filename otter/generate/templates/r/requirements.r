{% if not overwrite_requirements %}
install.packages(c(
    "gert",
    "usethis",
    "testthat",
    "startup"
), dependencies=TRUE, repos="http://cran.us.r-project.org")
{% endif %}{% if other_requirements %}
{{ other_requirements }}
{% endif %}