OK_FORMAT = True

test = {
	"name": "q5",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> negate(1 == 1)
					False
					>>> negate(True ^ False)
					False
					>>> negate(True ^ True)
					True
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
