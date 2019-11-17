test = {
	"name": "q3",
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
					"""
				},
			],
			"scored": False,
			"setup": "",
			"teardown": "",
			"type": "doctest"
		}, 
	]
}
