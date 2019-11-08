test = {
	"name": "q1_3H",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> cleaned_data.num_rows == 12376
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> len(cleaned_data.columns) == 5
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> cleaned_data.labels[2:5] == ("Capital Stock", "Real GDP", "Labor Force")
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.isclose(cleaned_data.row(6720).item("Real GDP"), 111266.3281)
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> cleaned_data.row(3).item("Labor Force") == -1
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> cleaned_data.row(2983).item("country") == "Cayman Islands"
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.isclose(cleaned_data.row(4202).item("Capital Stock"), 5691488.0)
					True
					""",
					"hidden": True,
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