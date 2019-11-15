test = {
	"name": "q3_2aH",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> sum(np.isclose(np.log(indexed_data.column("Indexed Y") / indexed_data.column("Indexed L")), log_ratios.column(2))) == 112 or sum(np.isclose(np.log(indexed_data.column("Indexed Y") / indexed_data.column("Indexed L")), log_ratios.column(3))) == 112
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> sum(np.isclose(np.log(indexed_data.column("Indexed K") / indexed_data.column("Indexed L")), log_ratios.column(2))) == 112 or sum(np.isclose(np.log(indexed_data.column("Indexed K") / indexed_data.column("Indexed L")), log_ratios.column(3))) == 112
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