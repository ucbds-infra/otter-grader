OK_FORMAT = True

test = {
	"name": "q3",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> import tqdm
					>>> print(tqdm.__name__)
					tqdm
					>>> 1 == 1
					True
					""",
					"hidden": False,
				}, {
					"code": r"""
					>>> import tqdm
					>>> print(tqdm.__name__)
					tqdm
					>>> 1 == 1
					True
					""",
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
