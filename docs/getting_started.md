# Getting Started

Otter has two major use cases: grading on the instructor's machine (local grading), and generating files to use Gradescope's autograding infrastructure.

## Local Grading

Once you've [installed otter](install.md), get started by creating some [test cases](tests_files.md) and creating a requirements.txt file (if necessary).

### Collecting Student Submissions

The first major decision is how you'll collect student submissions. You can collect these however you want, although otter has builtin compatibility with Gradescope and Canvas. If you choose either Gradescope or Canvas, just export the submissions and unzip that into some directory. If you are collecting another way, you'll need to create a metadata file. You can use either JSON or YAML format, and the structure is pretty simple: each element needs to have a filename and a student identifier. A sample YAML metadata file would be:

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

### Grading

Now that you've set up the directory, let's get down to grading. Go to the terminal, `cd` into your grading directory (`grading` in the example above), and let's build the `otter` command. The first thing we need is our notebooks path or `-p` argument. Otter assumes this is `./`, but our notebooks are located in `./submissions`, so we'll need `-p submissions` in our command. We also need a tests directory, which otter assumes is at `./tests`; because this is where our tests are, we're alright on this front, and don't need a `-t` argument.

Now we need to tell otter how we've structured our metadata. If you're using a Gradescope or Canvas export, just pass the `-g` or `-c` flag, respectively, with no arguments. If you're using a custom metadata file, as in our example, pass the `-j` or `-y` flag with the path to the metadata file as its argument; in our case, we will pass `-y submissions/meta.yml`.

At this point, we need to make a decision: do we want PDFs? If there are questions that need to be manually graded, it might be nice to generate a PDF of each submission so that it can be easily read; if you want to generate PDFs, pass one of the `--pdf`, `--tag-filter`, or `--html-filter` flags (cf. [PDFs](pdfs.md)). For our example, let's say that we *do* want PDFs.

Now that we've made all of these decisions, let's put our command together. Our command is:

```
otter -p submissions -y meta.yml --pdf -r requirements.txt -v
```

Note that we pass the `-r` flag to tell otter that we have a requirements.txt file that needs to be installed in the container, and the `-v` flag so that it prints verbose output. Once this command finishes running, you will end up with a new file and a new folder in your working directory:

```
| grading
  | - final_grades.csv
  | - requirements.txt
  | manual_submissions
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

Otter created the `final_grades.csv` file with the grades for each student, broken down by test, and the `manual_submissions` directory to house the PDF that was generated of each notebook.

**Congrats, you're done!** You can use the grades in the CSV file and the PDFs to complete grading however you want.

You can find more information about the command line utility [here](command-line.md)

## Gradescope

To get started using otter with Gradescope, create some [test cases](tests_files.md) and a requirements.txt file (if necessary). Once you have these pieces in place, put them into a directory along with any additional files that your notebook requires (e.g. data files), for example:

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

To create the zipfile for Gradescope, use the `otter gen` command after `cd`ing into the directory you created. For the directory above, once I've `cd`ed into `gradescope`, I would run the following to generate the zipfile:

```
otter gen -r requirements.txt data.csv utils.py
```

The `-r` flag indicates that we have additional requirements in a requirements.txt file and all of the additional files required are placed at the end of the command. Notice that we didn't indicate the path to the tests directory; this is because the default argument of the `-t` flag is `./tests`, so otter found them automatically.

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

You can find more information about Gradescope usage [here](gradescope.md)
