OK_FORMAT = True

test = {   'name': 'q1',
    'points': None,
    'suites': [   {   'cases': [   {   'code': '>>> isinstance(x, int)\nTrue',
                                       'failure_message': 'This is not an int.',
                                       'hidden': False,
                                       'locked': False,
                                       'points': 2,
                                       'success_message': 'Congrats you passed this test case!\\'},
                                   {'code': '>>> None\n', 'hidden': False, 'locked': False, 'points': 3, 'success_message': 'Congrats, this passed!'},
                                   {   'code': '>>> 0 < x < 100\nTrue',
                                       'failure_message': 'This should have passed.',
                                       'hidden': False,
                                       'locked': False,
                                       'points': 1,
                                       'success_message': 'Congrats your x value is in the correct range!'},
                                   {   'code': '>>> x\n2',
                                       'failure_message': 'This should have passed.',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 10,
                                       'success_message': 'Congrats you passed this test case!'},
                                   {'code': ">>> str(print(x))\n2\n'None'", 'hidden': True, 'locked': False, 'success_message': 'Congrats you passed this test case!'}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}