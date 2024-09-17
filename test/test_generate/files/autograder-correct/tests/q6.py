test = {
	"name": "q6",
	"points": 5,
	"hidden": True,
	"suites": [ 
		{
			"cases": [ 
				{
					"code": r"""
					>>> fib = fiberator()
					>>> next(fib) == 0 and next(fib) == 1
					True
					""",
					"hidden": False,
					"locked": False,
				}, 
				{
					"code": r"""
					>>> fib = fiberator()
					>>> for _ in range(10):
					... 	print(next(fib))
					0
					1
					1
					2
					3
					5
					8
					13
					21
					34
					""",
					"hidden": True,
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