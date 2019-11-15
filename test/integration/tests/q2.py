test = {
	"name": "q1",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> 1 == 1
					False
					""",
					"hidden": False,
					"locked": False,
				}, {
					"code": r"""
					>>> import tqdm
					>>> print(tqdm.__name__)
					tqdm
					"""
				}
			],
			"scored": False,
			"setup": "",
			"teardown": "",
			"type": "doctest"
		}, 
	]
}
