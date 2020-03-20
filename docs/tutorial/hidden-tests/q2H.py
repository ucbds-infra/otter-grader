test = {
	"name": "q2H",
	"points": 1,
	"hidden": True,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> f = fiberator()
					>>> assert next(f) == 0, ""
					>>> assert next(f) == 1, ""
					>>> assert next(f) == 1, ""
					>>> assert next(f) == 2, ""
					>>> assert next(f) == 3, ""
					>>> assert next(f) == 5, ""
					>>> assert next(f) == 8, ""
					>>> assert next(f) == 13, ""
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