# Metadata

When organizing submissions for grading, Otter supports two major categories of exports:
* 3rd party collection exports, or
* instructor-made metadata files

These two categories are broken down and described below.

## 3rd Party Exports

If you are using a grading service like Gradescope or an LMS like Canvas to collect submissions, Otter can interpret the export format of these 3rd party services in place of a metadata file. To use a service like Gradescope or Canvas, download the submissions for an assignment, unzip the provided file, and then proceed as described in [the command line usage](command-line.md) using the metadata flag corresponding to your chosen service.

For example, if I had a Canvas export, I would unzip it, `cd` into the unzipped directory, copy my tests to `./tests`, and run

```
otter -c
```

to grade the submissions (assuming no extra requirements, no PDF generation, and no support files required).

## Metadata Files

If you are not using a service like Gradescope or Canvas to collect submissions, instructors can also create a simple JSON- or YAML-formatted metadata file for their student's submissions and provide this to Otter.

The strucure of the metadata is quite simple: it is a list of 2-item dictionaries, where each dictionary has a student identifier stored as the `identifier` key and the filename of the student's submission as `filename`. An example of each is provided below.

YAML format:

```yaml
- identifier: 0
  filename: test-nb-0.ipynb
- identifier: 1
  filename: test-nb-1.ipynb
- identifier: 2
  filename: test-nb-2.ipynb
- identifier: 3
  filename: test-nb-3.ipynb
- identifier: 4
  filename: test-nb-4.ipynb
```

JSON format:

```json
[
  {
    "identifier": 0,
    "filename": "test-nb-0.ipynb"
  },
  {
    "identifier": 1,
    "filename": "test-nb-1.ipynb"
  },
  {
    "identifier": 2,
    "filename": "test-nb-2.ipynb"
  },
  {
    "identifier": 3,
    "filename": "test-nb-3.ipynb"
  },
  {
    "identifier": 4,
    "filename": "test-nb-4.ipynb"
  }
]
```

A JSON- or YAML-formatted metadata file is specified to Otter using the `-j` or `-y` flag, respectively. Each flag requires a  single argument that corresponds to the path to the metadata file. See the "Basic Usage" section of the [CLI documentation](command-line.md) for more information.
