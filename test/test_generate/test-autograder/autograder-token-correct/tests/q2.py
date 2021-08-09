test = {
	"name": "q2",
	"points": 2,
	"hidden": False,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> negate(True)
					False
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> negate(False)
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> negate("")
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> negate(1)
					False
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