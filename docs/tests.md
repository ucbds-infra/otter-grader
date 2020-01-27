# Test Files

Otter requires ok-formatted tests to check students' work against. These have a very specific format:

```python
test = {
	"name": "q1",       # name of the test
	"points": 1,        # number of points for the entire suite
	"suites": [         # list of suites, only 1 suite allowed
		{
			"cases": [              # list of test cases
				{
					"code": r"""    # test, formatted for Python interpreter
					>>> 1 == 1
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> 1 == 2
					False
					""",
					"hidden": False,
					"locked": False,
				}, 
			],
			"scored": False,
			"setup": "",
			"teardown": "",
			"type": "doctest"
		}, 
	]
}
```

You can find an online [ok test generator](https://oktests.herokuapp.com) that will assist you in generating this file.
