OK_FORMAT = True

test = {
	"name": "q1",
	"points": 0,
	"hidden": False,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> square(3)
					9
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> square(2.5)
					6.25
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> square(6)
					36
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> square(1.5)
					2.25
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