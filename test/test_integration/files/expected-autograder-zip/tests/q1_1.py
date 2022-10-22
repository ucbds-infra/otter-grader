OK_FORMAT = True

test = {   'name': 'q1_1',
    'points': None,
    'suites': [   {   'cases': [   {   'code': '>>> np.random.seed(1234)\n'
                                               '>>> x2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(corr(x2, y2), 0.6410799722591175)\n',
                                       'hidden': False,
                                       'locked': False},
                                   {   'code': '>>> np.random.seed(2345)\n'
                                               '>>> x2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(corr(x2, y2), -0.4008555019904271)\n',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 1}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
