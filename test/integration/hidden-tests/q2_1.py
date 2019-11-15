test = {
	"name": "q2_1",
	"points": 1,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> import numpy as np
					
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> len(country_array) == 4
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> "United States" in country_array
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> "China" in country_array
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> np.count_nonzero(np.isin(country_array, all_countries.column("Country"))) == 4
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> all_countries.where("Country", country_array.item(2)).column("Earliest Year") <= 1990
					array([ True])
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> all_countries.where("Country", country_array.item(3)).column("Earliest Year") <= 1990
					array([ True])
					""",
					"hidden": False,
					"locked": False,
				},
				{
					"code": r"""
					>>> len(comparison_data.group("country").column("country")) == 4
					True
					""",
					"hidden": False,
					"locked": False,
				},
				{
					"code": r"""
					>>> len(comparison_data.labels) == 5
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