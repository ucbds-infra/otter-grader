test = {
	"name": "q3_3aH",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> np.count_nonzero(china_x == log_ratios.where("country", "China").column("ln(K/L)")) == 28
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.count_nonzero(china_y == log_ratios.where("country", "China").column("ln(Y/L)")) == 28
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.count_nonzero(us_x == log_ratios.where("country", "United States").column("ln(K/L)")) == 28
					True
					""",
					"hidden": True,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.count_nonzero(us_y == log_ratios.where("country", "United States").column("ln(Y/L)")) == 28
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