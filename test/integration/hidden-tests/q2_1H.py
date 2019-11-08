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
				{
					"code": r"""
					>>> sum(comparison_data.group("country", min).column("year min") == 1990) == 4
					True
					""",
					"hidden": True,
					"locked": False,
				},
				{
					"code": r"""
					>>> sum(comparison_data.group("country").column("count")) == 28 * 4
					True
					""",
					"hidden": True,
					"locked": False,
				},
				{
					"code": r"""
					>>> np.isclose(comparison_data.group("country", max).where("country", "China").column("Labor Force max"), 792.575)
					array([ True])
					""",
					"hidden": True,
					"locked": False,
				},
				{
					"code": r"""
					>>> np.isclose(comparison_data.group("country", min).where("country", "United States").column("Real GDP min"), 9188685)
					array([ True])
					""",
					"hidden": True,
					"locked": False,
				},
				{
					"code": r"""
					>>> country_array.item(0) < country_array.item(1) < country_array.item(2) < country_array.item(3)
					True
					""",
					"hidden": True,
					"locked": False,
				},
				{
					"code": r"""
					>>> np.isclose(comparison_data.group("country", min).where("country", "United States").column("Real GDP min"), 9188685)
					array([ True])
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