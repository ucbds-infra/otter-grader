OK_FORMAT = True

test = {
	"name": "q2",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> 1 == 1
					False
					"""
				}, {
					"code": r"""
					>>> import tqdm
					>>> print(tqdm.__name__)
					tqdm
					""",
					"hidden": False,
					"locked": False,
				}
			],
			"scored": False,
			"setup": "",
			"teardown": "",
			"type": "doctest"
		}, 
	]
}
