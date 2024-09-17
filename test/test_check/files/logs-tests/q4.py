OK_FORMAT = True

test = {
	"name": "q4",
	"points": 1,
	"hidden": False,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> np.isclose(x, 39.0625)
					np.True_
					""",
					"hidden": True,
					"locked": False,
				}, 
			],
			"scored": False,
			"setup": "",
			"teardown": "",
			"type": "doctest"
		}
	]
}