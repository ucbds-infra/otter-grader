# Otter-Grader Documentation

```eval_rst
.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :hidden:

   install
   tutorial
   using_otter
   test_files
   otter_assign
   metadata_files
   otter_check
   otter_grade
   otter_generate
   pdfs
   The Otter API <otter>
   changelog
```

Otter-Grader is an open-source local grader from the Division of Computing, Data Science, and Society at the University of California, Berkeley. It is designed to be a scalable grader that utilizes parallel Docker containers on the instructor's machine in order to remove the traditional overhead requirement of a live server. It also supports student-run tests in Jupyter Notebooks and from the command line, and is compatible with Gradescope's proprietary autograding service.

Otter is a command-line tool organized into four basic commands: `assign`, `check`, `generate`, and `grade`. These commands provide functionality that allows instructors to create, distribute, and grade assignments locally or using a variety of learning management system (LMS) integrations. Otter also allows students to run publically distributed tests while working through assignments.
