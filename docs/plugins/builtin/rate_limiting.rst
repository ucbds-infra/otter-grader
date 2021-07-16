Rate Limiting
=============

This plugin allows instructors to limit the number of times students can submit to the autograder in 
any given window to prevent students from using the AG as an "oracle". This plugin has a required 
configuration ``allowed_submissions``, the number of submissions allowed during the window, and 
accepts optional configurations ``weeks``, ``days``, ``hours``, ``minutes``, ``seconds``, 
``milliseconds``, and ``microseconds`` (all defaulting to ``0``) to configure the size of the 
window. For example, to specify 5 allowed submissions per-day in your ``otter_config.json``:

.. code-block:: json

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

When a student submits, the window is caculated as a ``datetime.timedelta`` object and if the 
student has at least ``allowed_submissions`` in that window, the submission's results are hidden and 
the student is only shown a message; from the example above:

.. code-block::

    You have exceeded the rate limit for the autograder. Students are allowed 5 submissions every 1 
    days.

The results of submission execution are still visible to instructors.

If the student's submission is allowed based on the rate limit, the plugin outputs a message in the 
plugin report; from the example above:

.. code-block::

    Students are allowed 5 submissions every 1 days. You have {number of previous submissions} 
    submissions in that period.


``otter.plugins.builtin.RateLimiting`` Reference
------------------------------------------------

The actions taken by at hook for this plugin are detailed below.

.. autoclass:: otter.plugins.builtin.RateLimiting
    :members:
