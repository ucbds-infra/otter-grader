OK_FORMAT = True

test = {
	"name": "q3",
	"points": 2,
	"hidden": False,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> x
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> if x:
					... 	print("yep")
					... else:
					... 	print("nope")
					... 
					yep
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