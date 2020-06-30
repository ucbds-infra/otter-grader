# Tutorial

<!-- TODO: overhaul this -->

This tutorial can help you to verify that you have installed Otter correctly and introduce you to the general Otter workflow. 

## Verifying Your Installation

Once you have [installed](index.md) Otter, download [this zipfile](https://github.com/ucbds-infra/otter-grader/raw/master/docs/tutorial/tutorial.zip) and unzip it into some directory on your machine; I'll unzip it into my home directory, so that I have the following structure:

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

The first thing to note is that we have provided a [metadata file](otter_grade.html#metadata) that maps student identifiers to filenames in `tutorial/meta.json`. Note that metadata files are optional when using Otter, but we have provided one here to demonstrate their use.

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

Let's now construct a call to Otter that will grade these notebooks. We know that we have JSON-formatted metadata, so we'll be use the `-j` metadata flag. Our notebooks are in the current working directory, so we won't need to use the `-p` flag. However, we have two test directories: `tests`, which contains public tests, and `hidden-tests`, which contains *all* tests. We want to use the latter, so we'll need to specify `-t hidden-tests` in our call. The notebooks also contain a couple of written questions, and the [filtering](pdfs.md) is implemented using HTML comments, so we'll specify the `--html-filter` flag.

Let's run Otter:

```
$ otter grade -j meta.json -t hidden-tests --html-filter -v
```

(I've added the `-v` flag so that we get verbose output.) After this finishes running, there should be a new file and a new folder in the working directory: `final_grades.csv` should contain the grades for each file, and should look something like this:

```
identifier,file,manual,q1,q1H,q2,q2H,q3,q3H,total,possible
fails2Hidden,demo-fails2Hidden.ipynb,submission_pdfs/demo-fails2Hidden.pdf,1.0,2.0,1.0,0.0,1.0,0.0,5.0,8
fails1,demo-fails1.ipynb,submission_pdfs/demo-fails1.pdf,1.0,0.0,1.0,1.0,1.0,0.0,4.0,8
fails2,demo-fails2.ipynb,submission_pdfs/demo-fails2.pdf,1.0,2.0,0.0,0.0,1.0,0.0,4.0,8
fails3,demo-fails3.ipynb,submission_pdfs/demo-fails3.pdf,1.0,2.0,1.0,1.0,0.0,0.0,5.0,8
passesAll,demo-passesAll.ipynb,submission_pdfs/demo-passesAll.pdf,1.0,2.0,1.0,1.0,1.0,0.0,6.0,8
fails3Hidden,demo-fails3Hidden.ipynb,submission_pdfs/demo-fails3Hidden.pdf,1.0,2.0,1.0,1.0,1.0,0.0,6.0,8
```

Let's make that a bit prettier:

| identifier   | file                    | manual                                   | q1  | q1H | q2  | q2H | q3  | q3H | total | possible | 
|--------------|-------------------------|------------------------------------------|-----|-----|-----|-----|-----|-----|-------|----------| 
| fails2Hidden | demo-fails2Hidden.ipynb | submission_pdfs/demo-fails2Hidden.pdf | 1.0 | 2.0 | 1.0 | 0.0 | 1.0 | 0.0 | 5.0   | 8        | 
| fails1       | demo-fails1.ipynb       | submission_pdfs/demo-fails1.pdf       | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 0.0 | 4.0   | 8        | 
| fails2       | demo-fails2.ipynb       | submission_pdfs/demo-fails2.pdf       | 1.0 | 2.0 | 0.0 | 0.0 | 1.0 | 0.0 | 4.0   | 8        | 
| fails3       | demo-fails3.ipynb       | submission_pdfs/demo-fails3.pdf       | 1.0 | 2.0 | 1.0 | 1.0 | 0.0 | 0.0 | 5.0   | 8        | 
| passesAll    | demo-passesAll.ipynb    | submission_pdfs/demo-passesAll.pdf    | 1.0 | 2.0 | 1.0 | 1.0 | 1.0 | 0.0 | 6.0   | 8        | 
| fails3Hidden | demo-fails3Hidden.ipynb | submission_pdfs/demo-fails3Hidden.pdf | 1.0 | 2.0 | 1.0 | 1.0 | 1.0 | 0.0 | 6.0   | 8        | 

Note that public tests are worth 1 point in the above example and `q1H`, `q2H`, and `q3H` are worth 2, 1, and 2 points, respectively, for a total of 8 points (the `possible` column). In practice, you would probably have 0-point public tests, as hidden tests are meant to determine correctness. You should not that `fails2Hidden` failed `q2H` but not `q2`, and similarly for all other notebooks.

**Congratulations, that's how you use Otter!** If you've reached the end of this tutorial, you've correctly installed Otter and are ready to get grading.

## Using Otter

Now that you have verified that your isntallation is working, let's learn more about Otter's general workflow. Otter has two major use cases: grading on the instructor's machine (local grading), and generating files to use Gradescope's autograding infrastructure.

### Local Grading

Get started by creating some [test cases](test_files.md) and creating a requirements.txt file (if necessary).

#### Collecting Student Submissions

The first major decision is how you'll collect student submissions. You can collect these however you want, although Otter has builtin compatibility with Gradescope and Canvas. If you choose either Gradescope or Canvas, just export the submissions and unzip that into some directory. If you are collecting another way, you may want to create a metadata file. You can use either JSON or YAML format, and the structure is pretty simple: each element needs to have a filename and a student identifier. Metadata files are optional, and if not provided, grades will be primary keyed on the submission filename. A sample YAML metadata file would be:

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
- identifier: 5
  filename: test-nb-5.ipynb
...
```

### Support Files

If you have any files that are needed by the notebooks (e.g. data files), put these into the directory that contains the notebooks. You should also have your directory of tests nearby. At this stage, your directory should probably look something like this:

```
| grading
  | - requirements.txt
  | submissions
    | - meta.yml
    | - nb0.ipynb
    | - nb1.ipynb
    | - nb2.ipynb
    | - nb3.ipynb
    | - nb4.ipynb
    | - nb5.ipynb
    | - data.csv
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    | - q4.py
```

#### Grading

Now that you've set up the directory, let's get down to grading. Go to the terminal, `cd` into your grading directory (`grading` in the example above), and let's build the `otter grade` command. The first thing we need is our notebooks path or `-p` argument. Otter assumes this is `./`, but our notebooks are located in `./submissions`, so we'll need `-p submissions` in our command. We also need a tests directory, which Otter assumes is at `./tests`; because this is where our tests are, we're alright on this front, and don't need a `-t` argument.

Now we need to tell Otter how we've structured our metadata. If you're using a Gradescope or Canvas export, just pass the `-g` or `-c` flag, respectively, with no arguments. If you're using a custom metadata file, as in our example, pass the `-j` or `-y` flag with the path to the metadata file as its argument; in our case, we will pass `-y submissions/meta.yml`.

At this point, we need to make a decision: do we want PDFs? If there are questions that need to be manually graded, it might be nice to generate a PDF of each submission so that it can be easily read; if you want to generate PDFs, pass one of the `--pdf`, `--tag-filter`, or `--html-filter` flags (cf. [PDFs](pdfs.md)). For our example, let's say that we *do* want PDFs.

Now that we've made all of these decisions, let's put our command together. Our command is:

```
otter grade -p submissions -y meta.yml --pdf -v
```

Note that Otter automatically found our requirements file at `./requirements.txt`. If it had been in a different location, we would have needed to pass the path to it to the `-r` flag. Note also that we pass the `-v` flag so that it prints verbose output. Once this command finishes running, you will end up with a new file and a new folder in your working directory:

```
| grading
  | - final_grades.csv
  | - requirements.txt
  | submission_pdfs
    | - nb0.pdf
    | - nb1.pdf
    | - nb2.pdf
    | - nb3.pdf
    | - nb4.pdf
    | - nb5.pdf
  | submissions
    ...
  | tests
    ...
```

Otter created the `final_grades.csv` file with the grades for each student, broken down by test, and the `submission_pdfs` directory to house the PDF that was generated of each notebook.

**Congrats, you're done!** You can use the grades in the CSV file and the PDFs to complete grading however you want.

You can find more information about `otter grade` [here](otter_grade.md).

### Gradescope

To get started using Otter with Gradescope, create some [test cases](test_files.md) and a requirements.txt file (if necessary). Once you have these pieces in place, put them into a directory along with any additional files that your notebook requires (e.g. data files), for example:

```
| gradescope
  | - data.csv
  | - requirements.txt
  | - utils.py
  | tests
    | - q1.py
    | - q2.py
    ...
```

To create the zipfile for Gradescope, use the `otter generate` command after `cd`ing into the directory you created. For the directory above, once I've `cd`ed into `gradescope`, I would run the following to generate the zipfile:

```
otter generate data.csv utils.py
```

As above, Otter automatically found our requirements file at `./requirements.txt`. Notice also that we didn't indicate the path to the tests directory; this is because the default argument of the `-t` flag is `./tests`, so Otter found them automatically.

After this command finishes running, you should have a file called `autograder.zip` in the current working directory:

```
| gradescope
  | - autograder.zip
  | - data.csv
  | - requirements.txt
  | - utils.py
  | tests
    | - q1.py
    | - q2.py
    ...
```

To use this zipfile, create a Programming Assignment on Gradescope and upload this zipfile on the Configure Autograder page of the assignment. Gradescope will then build a Docker image on which it will grade each student's submission.

You can find more information about Gradescope usage [here](otter_generate.md).

