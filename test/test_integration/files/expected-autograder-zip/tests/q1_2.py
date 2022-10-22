OK_FORMAT = True

test = {   'name': 'q1_2',
    'points': None,
    'suites': [   {   'cases': [   {   'code': '>>> np.random.seed(1234)\n'
                                               '>>> x2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(slope(x2, y2), 0.853965497371089)\n',
                                       'hidden': False,
                                       'locked': False},
                                   {   'code': '>>> np.random.seed(1234)\n'
                                               '>>> x2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(intercept(x2, y2), 1.5592892975597108)\n',
                                       'hidden': False,
                                       'locked': False},
                                   {   'code': '>>> np.random.seed(2345)\n'
                                               '>>> x2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(slope(x2, y2), -0.5183482739336265)\n',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 0.5},
                                   {   'code': '>>> np.random.seed(2345)\n'
                                               '>>> x2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(intercept(x2, y2), 7.777051922080558)\n',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 0.5}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
