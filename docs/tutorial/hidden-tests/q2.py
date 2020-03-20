test = {
	"name": "q2",
	"points": 1,
	"hidden": False,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> f = fiberator()
					>>> assert next(f) == 0, ""
					>>> assert next(f) == 1, ""
					""",
					"hidden": False,
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