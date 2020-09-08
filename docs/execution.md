# Submission Execution

This section of the documentation describes the process by which submissions are executed in the autograder. Regardless of the method by which Otter is used, the autograding internals are all the same, although the execution differs slightly based on the file type of the submission.

## Notebooks

If students are submitting IPython notebooks (`.ipynb` files), they are executed as follows:

<ol>
    <li>Cells tagged with <code>otter_ignore</code> are removed from the notebook in memory.</li>
    <li>A dummy environment (a <code>dict</code>) is created and loaded with <code>IPython.display.display</code> and <code>sys</code>, which has the working directory appended to its path.</li>
    <li>If a seed is provided, NumPy and random are loaded into the environment as <code>np</code> and <code>random</code>, resp.</li>
    <li>The code cells are iterated through:
        <ol style="list-style-type: lower-alpha;">
            <li>The cell source is confrted into a list of strings line-by-line</li>
            <li>Lines that run cell magic (lines starting with <code>%</code>) or that call <code>ipywidgets.interact</code> are removed</li>
            <li>Lines that create an instance of <code>otter.Notebook</code> with a custom tests directory have their arguments transformed to set the correct path to the tests directory</li>
            <li>The lines are collected into a single multiline string</li>
            <li>If a seed is provided, the string is prepended with <code>f"np.random.seed({seed})\nrandom.seed({seed})\n"</code></li>
            <li>The code lines are run through an <code>IPython.core.inputsplitter.IPythonInputSplitter</code></li>
            <li>The string is run in the dummy environment with <code>otter.Notebook.export</code> and <code>otter.Notebook._log_event</code> patched so that they don't run</li>
            <li>If the run was successful, the cell contents are added to a collection string. If it fails, the error is ignored unless otherwise indicated.</li>
            <li>If the cell has metadata indicating that a check should be run after that cell, the code for the check is added.</li>
        </ol>
    </li>
    <li>The collection string is turned into an abstract syntax tree that is then transformed so that all calls of any form to <code>otter.Notebook.check</code> have their return values appended to a prenamed list which is in the dummy environemnt.</li>
    <li>The AST is compiled and executed in the dummy environment with stdout and stderr captured and <code>otter.Notebook.export</code> and <code>otter.Notebook._log_event</code> patched.</li>
    <li>If the run was successful, the cell contents are added to a collection string. If it fails, the error is ignored unless otherwise indicated.</li>
    <li>The dummy environment is returned.</li>
</ol>

The grades for each test are then collected from the list to which they were appended in the dummy environment and any additional tests are run against this resulting environment. Running in this manner has one main advantage: it is robust to variable name collisions. If two tests rely on a variable of the same name, they will not be stymied by the variable being changed between the tests, because the results for one test are collected from when that check is called rather than being run at the end of execution.

It is also possible to specify tests to run in the cell metadata without the need of explicit calls to `Notebook.check`. To do so, add an `otter` field to the cell metadata with the following structure:

```json
{
    "otter": {
        "tests": [
            "q1",
            "q2",
            "etc."
        ]
    }
}
```

The strings within `tests` should correspond to filenames within the tests directory (without the `.py` extension) as would be passed to `Notebook.check`. Inserting this into the cell metadata will cause Otter to insert a call to a covertly imported `Notebook` instance with the correct filename and collect the results _at that point of execution_, allowing for robustness to variable name collisions without explicit calls to `Notebook.check`. _Note that these tests are not currently seen by any checks in the notebook, so a call to `Notebook.check_all` will not include the results of these tests._

## Scripts

If students are submitting Python scripts, they are executed as follows:

<ol>
    <li>A dummy environment (a <code>dict</code>) is created and loaded with <code>sys</code>, which has the working directory appended to its path.</li>
    <li>If a seed is provided, NumPy and random are loaded into the environment as <code>np</code> and <code>random</code>, resp.</li>
    <li>The lines of the script are iterated through and lines that create an instance of <code>otter.Notebook</code> with a custom tests directory have their arguments transformed to set the correct path to the tests directory.</li>
    <li>The string is run in the dummy environment with <code>otter.Notebook.export</code> and <code>otter.Notebook._log_event</code> patched so that they don't run</li>
    <li>If the run was successful, the cell contents are added to a collection string. If it fails, the error is ignored unless otherwise indicated.</li>
    <li>The collection string is turned into an abstract syntax tree that is then transformed so that all calls of any form to <code>otter.Notebook.check</code> have their return values appended to a prenamed list which is in the dummy environemnt.</li>
    <li>The AST is compiled and executed in the dummy environment with stdout and stderr captured and <code>otter.Notebook.export</code> and <code>otter.Notebook._log_event</code> patched.</li>
    <li>If the run was successful, the cell contents are added to a collection string. If it fails, the error is ignored unless otherwise indicated.</li>
    <li>The dummy environment is returned.</li>
</ol>

Similar to notebooks, the grades for tests are collected from the list in the returned environment and additional tests are run against it.

## Logs

If grading from logs is enabled, the logs are xecuted in the following manner:

<ol>
    <li>A dummy environment (a <code>dict</code>) is created and loaded with <code>sys</code>, which has the working directory appended to its path, and an <code>otter.Notebook</code> instance named <code>grader</code>.</li>
    <li>The lines of each code cell are iterated through and each import statement is executed in the dummy environment.</li>
    <li>Each entry in the log is iterated through and has its serialized environments deserialized and loaded into the dummy environment. If variable type checking is enabled, and variables whose types do not match their prespecified type are not loaded.</li>
    <li>The grader in the dummy environment has its <code>check</code> method called and the results are collected in a list in the dummy environment.</li>
    <li>A message is printed to stdout indicating which questions were executed from the log.</li>
    <li>The dummy environment is returned.</li>
</ol>

Similar to the above file types, the grades for tests are collected from the list in the returned environment and additional tests are run against it.
