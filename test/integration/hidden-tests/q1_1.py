test = {
	"name": "q1_1",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> all_countries.num_rows == 182
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> all_countries.row(23)[0] < all_countries.row(55)[0]
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> all_countries.labels == ("Country", "Earliest Year")
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> data.where("year", all_countries.row(128)[1]).where("country", all_countries.row(128)[0]).column("cgdpe") != -1
					array([ True])
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> data.where("year", all_countries.row(134)[1]).where("country", all_countries.row(134)[0]).column("cgdpe") != -1
					array([ True])
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> data.where("year", all_countries.row(134)[1] - 1).where("country", all_countries.row(134)[0]).column("cgdpe") == -1
					array([ True])
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