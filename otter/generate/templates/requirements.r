{% if not overwrite_requirements %}
install.packages(c(
    "usethis",
    "testthat",
    "startup"
), repos="http://cran.us.r-project.org")
{% endif %}{% if other_requirements %}
{{ other_requirements }}
{% endif %}