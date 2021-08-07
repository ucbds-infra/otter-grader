Google Sheets Grade Override
============================

This plugin allows you to override test case scores during grading by specifying the new score in a 
Google Sheet that is pulled in. To use this plugin, you must set up a Google Cloud project and 
obtain credentials for the Google Sheets API. This plugin relies on ``gspread`` to interact with the 
Google Sheets API and `its documentation <https://gspread.readthedocs.io/en/latest/>`_ contains 
instructions on how to obtain credentials. Once you have created credentials, download them as a 
JSON file.

This plugin requires two configurations: the path to the credentials JSON file and the URL of the 
Google Sheet. The former should be entered with the key ``credentials_json_path`` and the latter 
``sheet_url``; for example, in Otter Assign:

.. code-block:: yaml

    plugins:
        - otter.plugins.builtin.GoogleSheetsGradeOverride:
            credentials_json_path: /path/to/google/credentials.json
            sheet_url: https://docs.google.com/some/google/sheet

The first tab in the sheet is assumed to be the override information.

During Otter Generate, the plugin will read in this JSON file and store the relevant data in the 
``otter_config.json`` for use during grading. The Google Sheet should have the following format:

.. list-table::
    :header-rows: 1

    * - Assignment ID
      - Email
      - Test Case
      - Points
      - PDF
    * - 123456
      - student@univ.edu
      - q1a - 1
      - 1
      - false

* ``Assignment ID`` should be the ID of the assignment on Gradescope (to allow one sheet to be used 
  for multiple assignments)
* ``Email`` should be the student's email address on Gradescope
* ``Test Case`` should be the name of the test case as a string (e.g. if you have a test file 
  ``q1a.py`` with 3 test cases, overriding the second case would be ``q1a - 2``)
* ``Points`` should be the point value to assign the student for that test case
* ``PDF`` should be whether or not a PDF should be re-submitted (to prevent losing manual grades on 
  Gradescope for regrade requests)

Note that the use of this plugin requires specifying ``gspread`` in your requirements, as it is 
not included by default in Otter's container image.


``otter.plugins.builtin.GoogleSheetsGradeOverride`` Reference
-------------------------------------------------------------

The actions taken by at hook for this plugin are detailed below.

.. autoclass:: otter.plugins.builtin.GoogleSheetsGradeOverride
    :members:
