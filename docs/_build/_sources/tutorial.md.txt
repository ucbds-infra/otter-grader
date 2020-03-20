# Tutorial

This tutorial can help you to verify that you have installed Otter correctly and introduce you to the general Otter workflow. Once you have [installed](install.md) Otter, download [this zipfile](https://raw.githubusercontent.com/ucbds-infra/otter-grader/docs/tutorial/tutorial.zip) and unzip it into some directory on your machine; I'll unzip it into my home directory, so that I have the following structure:

```
| ~
  | tutorial
    | - demo-fails1.ipynb
    | - demo-fails2.ipynb
    | - demo-fails2Hidden.ipynb
    | - demo-fails3.ipynb
    | - demo-fails3Hidden.ipynb
    | - demo-passesAll.ipynb
    | - meta.json
    | hidden-tests
      | - q1.py
      | - q1H.py
      | - q2.py
      | - q2H.py
      | - q3.py
      | - q3H.py
    | tests
      | - q1.py
      | - q2.py
      | - q3.py
```

`cd` into `tutorial` and let's get started.

The first thing to note is that we have provided a [metadata file](metadata.md) that maps student identifiers to filenames in `tutorial/meta.json`:

```json
[
    {
        "identifier": "passesAll",
        "filename": "demo-passesAll.ipynb"
    },
    {
        "identifier": "fails1",
        "filename": "demo-fails1.ipynb"
    },
    {
        "identifier": "fails2",
        "filename": "demo-fails2.ipynb"
    },
    {
        "identifier": "fails2Hidden",
        "filename": "demo-fails2Hidden.ipynb"
    },
    {
        "identifier": "fails3",
        "filename": "demo-fails3.ipynb"
    },
    {
        "identifier": "fails3Hidden",
        "filename": "demo-fails3Hidden.ipynb"
    }
]
```

The filename and identifier of each notebook indicate which tests should be failing; for exampl, `demo-fails2.ipynb` fails `q2` and `q2H`, and `demo-fails2Hidden.ipynb` fails `q2H`.

Let's now construct a call to `otter` that will grade these notebooks. We know that we have JSON-formatted metadata, so we'll be use the `-j` metadata flag. Our notebooks are in the current working directory, so we won't need to use the `-p` flag. However, we have two test directories: `tests`, which contains public tests, and `hidden-tests`, which contains *all* tests. We want to use the latter, so we'll need to specify `-t hidden-tests` in our call. The notebooks also contain a couple of written questions, and the [filtering](pdfs.md) is implemented using HTML comments, so we'll specify the `--html-filter` flag.

Let's run Otter:

```
$ otter -j meta.json -t hidden-tests --html-filter -v
```

(I've added the `-v` flag so that we get verbose output.) After this finishes running, there should be a new file and a new folder in the working directory: `final_grades.csv` should contain the grades for each file, and should look something like this:

```
identifier,file,manual,q1,q1H,q2,q2H,q3,q3H,total,possible
fails2Hidden,demo-fails2Hidden.ipynb,manual_submissions/demo-fails2Hidden.pdf,1.0,2.0,1.0,0.0,1.0,0.0,5.0,8
fails1,demo-fails1.ipynb,manual_submissions/demo-fails1.pdf,1.0,0.0,1.0,1.0,1.0,0.0,4.0,8
fails2,demo-fails2.ipynb,manual_submissions/demo-fails2.pdf,1.0,2.0,0.0,0.0,1.0,0.0,4.0,8
fails3,demo-fails3.ipynb,manual_submissions/demo-fails3.pdf,1.0,2.0,1.0,1.0,0.0,0.0,5.0,8
passesAll,demo-passesAll.ipynb,manual_submissions/demo-passesAll.pdf,1.0,2.0,1.0,1.0,1.0,0.0,6.0,8
fails3Hidden,demo-fails3Hidden.ipynb,manual_submissions/demo-fails3Hidden.pdf,1.0,2.0,1.0,1.0,1.0,0.0,6.0,8
```

Let's make that a bit prettier:

| identifier   | file                    | manual                                   | q1  | q1H | q2  | q2H | q3  | q3H | total | possible | 
|--------------|-------------------------|------------------------------------------|-----|-----|-----|-----|-----|-----|-------|----------| 
| fails2Hidden | demo-fails2Hidden.ipynb | manual_submissions/demo-fails2Hidden.pdf | 1.0 | 2.0 | 1.0 | 0.0 | 1.0 | 0.0 | 5.0   | 8        | 
| fails1       | demo-fails1.ipynb       | manual_submissions/demo-fails1.pdf       | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 0.0 | 4.0   | 8        | 
| fails2       | demo-fails2.ipynb       | manual_submissions/demo-fails2.pdf       | 1.0 | 2.0 | 0.0 | 0.0 | 1.0 | 0.0 | 4.0   | 8        | 
| fails3       | demo-fails3.ipynb       | manual_submissions/demo-fails3.pdf       | 1.0 | 2.0 | 1.0 | 1.0 | 0.0 | 0.0 | 5.0   | 8        | 
| passesAll    | demo-passesAll.ipynb    | manual_submissions/demo-passesAll.pdf    | 1.0 | 2.0 | 1.0 | 1.0 | 1.0 | 0.0 | 6.0   | 8        | 
| fails3Hidden | demo-fails3Hidden.ipynb | manual_submissions/demo-fails3Hidden.pdf | 1.0 | 2.0 | 1.0 | 1.0 | 1.0 | 0.0 | 6.0   | 8        | 

Note that public tests are worth 1 point in the above example and `q1H`, `q2H`, and `q3H` are worth 2, 1, and 2 points, respectively, for a total of 8 points (the `possible` column). In practice, you would probably have 0-point public tests, as hidden tests are meant to determine correctness. You should not that `fails2Hidden` failed `q2H` but not `q2`, and similarly for all other notebooks.

**Congratulations, that's how you use Otter!** If you've reached the end of this tutorial, you've correctly installed Otter and are ready to get grading. For more information about using Otter, see [Using Otter](using_otter.md).
