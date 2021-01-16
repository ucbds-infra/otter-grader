# Built-In Plugins

Otter comes with a few built-in plugins to optionally extend its own functionality. These plugins are documented here. **Note:** To use these plugins, specify the importable names _exactly_ as seen here (i.e. `otter.plugins.builtin.GoogleSheetsGradeOverride`, not `otter.plugins.builtin.grade_override.GoogleSheetsGradeOverride`).

## Google Sheets Grade Override

This plugin allows you to override test case scores during grading by specifying the new score in a Google Sheet that is pulled in. To use this plugin, you must set up a Google Cloud project and obtain credentials for the Google Sheets API. This plugin relies on `gspread` to interact with the Google Sheets API and [its documentation](https://gspread.readthedocs.io/en/latest/) contains instructions on how to obtain credentials. Once you have created credentials, download them as a JSON file.

This plugin requires two configurations: the path to the credentials JSON file and the URL of the Google Sheet. The former should be entered with the key `credentials_json_path` and the latter `sheet_url`; for example, in Otter Assign:

```yaml
plugins:
    - otter.plugins.builtin.GoogleSheetsGradeOverride:
        credentials_json_path: /path/to/google/credentials.json
        sheet_url: https://docs.google.com/some/google/sheet
```

The first tab in the sheet is assumed to be the override information.

During Otter Generate, the plugin will read in this JSON file and store the relevant data in the `otter_config.json` for use during grading. The Google Sheet should have the following format:

| Assignment ID | Email            | Test Case | Points | PDF          |
|---------------|------------------|-----------|--------|--------------|
| 123456        | student@univ.edu | q1a - 1   | 1      | false        |

* `Assignment ID` should be the ID of the assignment on Gradescope (to allow one sheet to be used for multiple assignments)
* `Email` should be the student's email address on Gradescope
* `Test Case` should be the name of the test case as a string (e.g. if you have a test file `q1a.py` with 3 test cases, overriding the second case would be `q1a - 2`)
* `Points` should be the point value to assign the student for that test case
* `PDF` should be whether or not a PDF should be re-submitted (to prevent losing manual grades on Gradescope for regrade requests)

**Note that the use of this plugin requires specifying `gpsread` in your requirements, as it is not included by default in Otter's container image.**

The actions taken by at hook for this plugin are detailed below.

### `otter.plugins.builtin.GoogleSheetsGradeOverride` Reference

```eval_rst
.. autoclass:: otter.plugins.builtin.GoogleSheetsGradeOverride
    :members:
```

## Rate Limiting

This plugin allows instructors to limit the number of times students can submit to the autograder in any given window to prevent students from using the AG as an "oracle". This plugin has a required configuration `allowed_submissions`, the number of submissions allowed during the window, and accepts optional configurations `weeks`, `days`, `hours`, `minutes`, `seconds`, `milliseconds`, and `microseconds` (all defaulting to `0`) to configure the size of the window. For example, to specify 5 allowed submissions per-day in your `otter_config.json`:

```json
{
    "plugins": [
        {
            "otter.plugins.builtin.RateLimiting": {
                "allowed_submissions": 5,
                "days": 1
            }
        }
    ]
}
```

When a student submits, the window is caculated as a `datetime.timedelta` object and if the student has at least `allowed_submissions` in that window, the submission's results are hidden and the student is only shown a message; from the example above:

```
You have exceeded the rate limit for the autograder. Students are allowed 5 submissions every 1 days.
```

The results of submission execution are still visible to instructors.

If the student's submission is allowed based on the rate limit, the plugin outputs a message in the plugin report; from the example above:

```
Students are allowed 5 submissions every 1 days. You have {number of previous submissions} submissions in that period.
```

The actions taken by at hook for this plugin are detailed below.

### `otter.plugins.builtin.RateLimiting` Reference

```eval_rst
.. autoclass:: otter.plugins.builtin.RateLimiting
    :members:
```
