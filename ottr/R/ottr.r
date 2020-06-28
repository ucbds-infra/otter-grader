#===================================================================================================
# Otter-Grader Script for Grading R and Rmd files
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# Helpful Global Variables
#---------------------------------------------------------------------------------------------------

VALID_EXPR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJLKMNOPQRSTUVWXYZ1234567890._"


#---------------------------------------------------------------------------------------------------
# Helpful Classes for Storing Suite and Case Results
#---------------------------------------------------------------------------------------------------

test_case_result = setRefClass(
  "test_example",
  fields = c("name", "result", "hidden", "passed", "points"),
  methods = list(
    repr = function() {
      if (passed) return("All tests passed!")
      output = ""
      for (j in seq_along(result)) {
        test_name = result[[j]]$test
        if (!methods::is(result[[j]], "expectation_success")) {
          test_output = paste0("    ", paste(strsplit(as.character(result[[j]]), "\n")[[1]], collapse="\n    "))
          output = paste0(
            output,
            "Test ", test_name, " failed:\n",
            test_output
          )
        }
      }
      return(output)
    },
    get_points = function() points,
    get_name = function() name,
    get_score = function() ifelse(passed, points, 0)
  )
)

test_suite_result = setRefClass(
  "test_suite_result",
  fields = c("case_results", "raw_results", "filename", "metadata"),
  methods = list(
    repr = function() {
      # if all tests passed, just return that
      if (get_score() == 1) {
        return("All tests passed!")
      }

      # otherwise, iterate through results and put hints together
      output = c()
      for (result in case_results) {
        if (!result$passed) {
          output = c(output, result$repr())
        }
      }
      return(paste0(output, collapse="\n\n"))
    },
    failed_hidden_cases = function() {
      cases = c()
      for (case_result in case_results) {
        meta = get_case_metadata(metadata, case_result$name)
        if (meta[["hidden"]] && !case_result$passed) {
          cases = c(cases, case_result)
        }
      }
      return(cases)
    },
    failed_public_cases = function() {
      cases = c()
      for (case_result in case_results) {
        meta = get_case_metadata(metadata, case_result$name)
        if (!meta[["hidden"]] && !case_result$passed) {
          cases = c(cases, case_result)
        }
      }
      return(cases)
    },
    get_score = function() {
      earned = 0; possible = 0;
      for (case in case_results) {
        earned = earned + case$get_score()
        possible = possible + case$get_points()
      }
      return(ifelse(possible == 0, 0, earned / possible))
    },
    get_name = function() {
      return(metadata[["name"]])
    },
    get_points = function() {
      return(sum(sapply(case_results, getElement, "points")))
    },
    get_basename = function() filename,
    failed_any_public = function() {
      for (result in case_results) {
        if (!result$hidden && !result$passed) {
          return(TRUE)
        }
      }
      return(FALSE);
    }
  )
)


#---------------------------------------------------------------------------------------------------
# Test Metadata and Result Parsers and Getters
#---------------------------------------------------------------------------------------------------

#' Load test suite metadata from a file
#'
#' Executes the script FILE expression-by-expression and extracts the global variable test_metadata.
#' This string is run through a YAML parser to construct a list containing the metadata specifications
#' for that test suite. The global key `name` should be defined and `cases` should be a list of
#' dictionaries with keys `name` and `hidden`. The key `case[[int]][["name"]]` should match a name
#' passed to a call to test_that.
#'
#' For example, the test suite might have the following contents:
#'
#' ```r
#' library(testthat)
#'
#' test_metadata = "
#' name: q1
#' cases:
#'   - name: q1a
#'     hidden: false
#'   - name: q1b
#'     hidden: true
#' "
#'
#' test_that("q1a", {...})
#'
#' test_that("q1b", {...})
#' ```
#'
#' @param file Path to a test suite file
#' @return The parse test suite metadata
load_test_metadata = function(file) {
  env = new.env()

  exps = parse(file=file)

  for (i in seq_along(exps)) {
    exp = exps[i]
    tryCatch(
      eval(exp, envir=env),
      error = function(e) {}
    )
  }

  return(yaml::yaml.load(env$test_metadata))
}

#' Get the entry for the test case with name `case_name` from `test_metadata`
#'
#' @param test_metadata The parsed test metadata
#' @param case_name The name of the desired case
#' @return The configuration for test case CASE_NAME
get_case_metadata = function(test_metadata, case_name) {
  cases = test_metadata[["cases"]]
  for (l in cases) {
    if (l[["name"]] == case_name) {
      return(l)
    }
  }
  stop(paste0("Test case ", case_name, " not found"))
}

# PYTHONIC STRUCTURE OF suite_results:
#   suite_results = [
#     {
#       "file": file_name,
#       "test": test_name,
#       "results": [  # this key is case_results
#         {
#           "message": test_output,
#           "test": test_name
#         }
#       ]
#     }
#   ]
#
# Notes:
# - suite_results corresponds to a whole test file
# - case_results corresponds to a single test_that call within the test file
# - case_results[int] corresponds to a single expectation within a test_that block

#' Parse output from `testthat::ListReporter` and return an instance of the ref class test_suite_results
#' constructed from this output
#'
#' @param suite_results The output from a `testthat::ListReporter` as a list
#' @param test_metadata The parsed metadata from the test suite
#' @param num_cases The number of test cases in the suite
#' @return The parsed results for the test suite
parse_suite_results = function(suite_results, test_metadata, num_cases) {
  # initialize values
  num_passed_tests = 0
  results = list()

  for (i in seq_along(suite_results)) {
    case_results = suite_results[[i]]$results

    # test case passes if all its expectations passed
    passed = all(sapply(case_results, methods::is, "expectation_success"))

    # create a test_case_result instance for this test_that call
    hidden = get_case_metadata(test_metadata, suite_results[[i]]$test)[["hidden"]]
    points = get_case_metadata(test_metadata, suite_results[[i]]$test)[["points"]]
    results[[i]] = test_case_result(name=suite_results[[i]]$test, result=case_results,
                                    hidden=hidden, passed=passed, points=points)
    num_passed_tests = num_passed_tests + ifelse(passed, 1, 0)
  }

  # calculate % score for this test file: number passed cases / number of cases
  test_score = ifelse(num_cases == 0, 0, num_passed_tests / num_cases)

  # create a test_suite_result instance
  result = test_suite_result(
    case_results=results,
    metadata=test_metadata,
    filename=suite_results[[1]]$file
  )

  return(result)
}


#---------------------------------------------------------------------------------------------------
# Executors and Graders
#---------------------------------------------------------------------------------------------------

#' Execute checks in a test suite and return the test_suite_result object from executing the test.
#' Optionally prints results of the test to console.
#'
#' @param test_file Path to a test file
#' @param test_env An environment against which to run tests
#' @param show_results Whether to print the results to stdout
#' @return The parsed test results for the suite
#' @export
check = function(test_file, test_env, show_results) {

  # need to specify a test file
  if (missing(test_file)) {
      stop("must have a test file")
  }

  # if show_results is not passed, default to TRUE
  if (missing(show_results)) {
    show_results = TRUE
  }

  # load test metadata from test file
  test_metadata = load_test_metadata(test_file)

  # grab the calling frame
  if (missing(test_env)) {
    test_env = parent.frame(1)
  }

  # redirect stdout so that testthat doesn't print
  testthat::capture_output({
    # get number of test cases in test_file
    num_cases = length(testthat::test_file(test_file, reporter = "minimal"))

    # test the variables in test_env
    lr <- testthat::ListReporter$new()
    out <- testthat::test_file(test_file, reporter = lr, env = test_env)
    suite_results <- lr$results$as_list()
  })

  # parse the output from ListReporter into test_suite_result object
  suite_results = parse_suite_results(suite_results, test_metadata, num_cases)
  suite_results$raw_results = lr$results$as_list()

  # print out suite_results if show_results is TRUE
  if (show_results) {
    cat(suite_results$repr())
  }

  # return the test suite results
  return(suite_results)
}

#' Execute a string as an R script and return the environment from that execution.
#'
#' Converts a string to an AST and executes that script in a dummy environment for running test cases
#' against. Transforms all expressions of the form `. = otter::check(...)` by replacing the `.` with
#' an index into a list in the environment with name `check_results_{SECRET}` to collect the
#' test_suite_result objects generated from those checks. (This helps to handle variable name collisions
#' in tests when grading a script.)
#'
#' @param script The string to be executed
#' @param secret The string to be appended to the name `check_results_` as the list name to collect
#' results
#' @return The global environment after executing the script
execute_script = function(script, secret) {
  # convert script to a list of expressions
  tree = as.list(parse(text=script))

  # create check result collection list name as expression
  list_name = parse(text=paste0("check_results_", secret))[[1]]

  # wrap calls of form `. = otter::check(...)` to append to list and convert back to string
  tree = update_ast_check_calls(tree, list_name)
  updated_script = paste(tree, collapse="\n")

  # create dummy env for execution and add check_results_XX list
  test_env = new.env()
  test_env[[as.character(list_name)]] = list()

  # run the script, capturing stdout, and return the environment
  testthat::capture_output({
    for (expr in as.list(parse(text=updated_script))) {
      tryCatch(
        eval(expr, envir=test_env),
        error = function(e){}
      )
    }
  })
  return(test_env)
}

#' Execute a script, parse check outputs, and run additional tests specified by the glob pattern
#' `tests_glob` on the test environment.
#'
#' @param script_path The path to the script
#' @param tests_glob The pattern to search for extra tests
#' @param secret The string to be appended to the name `check_results_` as the list name to collect
#' results (optional)
#' @return The list of test_suite_result objects after executing tests referenced in the script
#' and those specified by `tests_glob`
#' @export
grade_script = function(script_path, tests_glob, secret) {
  # convert script to a string
  script = paste(readLines(script_path), collapse="\n")

  # create a secret with if unspecified
  if (missing(secret)) {
    secret = make_secret()
  }

  # run the script and extract results from env, capturing stdout
  testthat::capture_output({
    test_env = execute_script(script, secret)
    results = test_env[[paste0("check_results_", secret)]]
  })

  # run the tests in tests_glob on the env, collect in results
  num_embedded_tests = length(results)
  tests_glob = Sys.glob(tests_glob)
  i = 1
  for (test_file in tests_glob) {
    already_tested = sapply(results, function(r) tolower(r$filename))
    if (!(basename(test_file) %in% already_tested)) {
      results[[i + num_embedded_tests]] = check(test_file, test_env, FALSE)
      i = i + 1
    }
  }
  return(results)
}

#' Run autograder in a Gradescope container and return the results as a properly-formatted JSON
#' string
#'
#' @param script_path The path to the script
#' @param secret The string to be appended to the name `check_results_` as the list name to collect
#' results (optional)
#' @return The JSON string
#' @export
run_gradescope = function(script_path, secret) {
  if (missing(secret)) {
    secret = make_secret()
  }
  results = grade_script(script_path, "/autograder/source/tests/*.[Rr]", secret)
  results = results_to_list(results)
  return(jsonlite::toJSON(results), auto_unbox=TRUE, pretty=TRUE)
}


#---------------------------------------------------------------------------------------------------
# Utilities
#---------------------------------------------------------------------------------------------------

#' Traverse an AST (a list of expressions) and change calls of the form `. = otter::check(...)` so
#' that they are appended to a list with name `list_name`.
#'
#' If `list_name` is `check_results_XX`, then `. = otter::check(...)` becomes
#' `check_results_XX[[<int>]] = otter::check(...)`, where `<int>` is an integer
#'
#' @param tree The tree to traverse
#' @param list_name The quoted name of the list
#' @return The tree with substitutions made
update_ast_check_calls = function(tree, list_name) {
  list_idx = 1
  for (i in seq_along(tree)) {
    expr = tree[[i]]
    if (class(expr) == "=") {
      right_expr = expr[[3]]
      call = right_expr[[1]]
      if (length(call) >= 3) {
        pkg = call[[2]]
        fn = call[[3]]
        if (pkg == "otter" && fn == "check") {
          env = new.env()
          env$list_name = list_name
          env$list_idx = list_idx
          new_left_expr = substitute(list_name[[list_idx]], env)
          expr[[2]] = new_left_expr
          list_idx = list_idx + 1
        }
      }
    }
    tree[[i]] = expr
  }
  return(tree)
}

#' Randomly generate a string of `n_chars` sampled at random from `valid_chars`.
#'
#' @param n_chars The number of characters in the string; defaults to 6
#' @param valid_chars A string of characters to choose from; defaults to all alphanumerals, `.`, and
#' `_`
#' @return The generated string
make_secret = function(n_chars, valid_chars) {
  if (missing(n_chars)) {
    n_chars = 6
  }
  if (missing(valid_chars)) {
    valid_chars = strsplit(VALID_EXPR_CHARS, "")[[1]]
  }

  chars = sample(valid_chars, n_chars, replace=T)
  return(paste(chars, collapse=""))
}

# GRADESCOPE OUTPUT FORMAT:
#   output["tests"] += [{
#     "name" : key + " - Hidden",
#     "score" : hidden_score,
#     "max_score": hidden_possible,
#     "visibility": hidden_test_visibility,
#     "output": repr(scores[key]["test"])
#   }]

#' Convert a list of `test_suite_result` objects to a JSON-like object of the correct form for writing
#' results for Gradescope.
#'
#' @param results The list of `test_suite_result`s
#' @return The generated list
results_to_list = function(results) {
  out = list()
  out[["tests"]] = list()
  out_idx = 1
  for (i in seq_along(results)) {
    suite_results = results[[i]]
    for (j in seq_along(suite_results$case_results)) {
      case_results = suite_results$case_results[[j]]
      l = list()
      l[["name"]] = case_results$get_name()
      l[["score"]] = case_results$get_score()
      l[["max_score"]] = case_results$get_points()
      l[["visibility"]] = ifelse(case_results$hidden, "hidden", "visible")
      l[["output"]] = case_results$repr()
      out[["tests"]][[out_idx]] = l
      out_idx = out_idx + 1
    }
  }
  return(out)
}

#' Export a list of `test_suite_result`s to a JSON string
#'
#' @param results The list of result objects
#' @return The JSON string
#' @export
results_to_json = function(results) {
  results = results_to_list(results)
  return(jsonlite::toJSON(results, auto_unbox = T, pretty = T))
}
