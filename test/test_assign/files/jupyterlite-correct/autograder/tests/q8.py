OK_FORMAT = True

test = {   'name': 'q8',
    'points': None,
    'suites': [   {   'cases': [   {   'code': '>>> len(z) == 10\nTrue',
                                       'failure_message': 'Make sure the length is 10.',
                                       'hidden': False,
                                       'locked': False,
                                       'points': 10,
                                       'success_message': 'The length is correct!'},
                                   {   'code': '>>> np.allclose(z, [3.07316461, 3.06854049, 4.48392454, 0.17343951, 0.55016433,\n'
                                               '...        2.87542494, 1.97433776, 4.62849467, 2.18395185, 1.1753926 ])\n'
                                               'False',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 2,
                                       'success_message': 'Congrats you passed this test case!'}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
