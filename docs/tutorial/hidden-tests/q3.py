test = {
	"name": "q3",
	"points": 1,
	"hidden": False,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> len(data["flavor"].unique()) == 4
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> for l in ["chocolate", "vanilla", "strawberry", "mint"]:
					... 	assert l in data["flavor"].unique()
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> assert type(price_by_flavor) == pd.Series
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> assert len(price_by_flavor) == 4
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