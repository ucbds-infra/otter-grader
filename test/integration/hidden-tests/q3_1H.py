test = {
	"name": "q3_1H",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> list_of_countries = indexed_data.group("country").column("country")
					>>> for country in list_of_countries:
					...		if country != "China" and country != "United States":
					...			break
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> indexed_data.where("country", country).where("year", 2011).column(2) == 100
					array([ True])
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> indexed_data.where("country", country).where("year", 2011).column(3) == 100
					array([ True])
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> indexed_data.where("country", country).where("year", 2011).column(4) == 100
					array([ True])
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.count_nonzero(indexed_data.where("country", "China").column(2) > 1) == 28
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.count_nonzero(indexed_data.where("country", "United States").column(3) > 1) == 28
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.count_nonzero(indexed_data.where("country", "China").column(4) > 1) == 28
					True
					""",
					"hidden": False,
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