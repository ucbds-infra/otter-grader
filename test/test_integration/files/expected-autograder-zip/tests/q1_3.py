OK_FORMAT = True

test = {   'name': 'q1_3',
    'points': None,
    'suites': [   {   'cases': [   {   'code': '>>> assert len(y_hat) == len(y)\n>>> assert x.shape == (30000,)\n>>> assert 0.1 <= beta_1 <= 0.2\n>>> assert 23000 <= beta_0 <= 25000\n',
                                       'hidden': False,
                                       'locked': False},
                                   {'code': '>>> assert np.isclose(beta_1, 0.16199038569776522)\n', 'hidden': True, 'locked': False, 'points': 1},
                                   {'code': '>>> assert np.isclose(beta_0, 24092.480872897704)\n', 'hidden': True, 'locked': False, 'points': 1},
                                   {   'code': '>>> np.random.seed(1001)\n'
                                               '>>> sub_y = np.random.choice(y_hat, 5)\n'
                                               '>>> assert np.allclose(sub_y, [105087.67372178, 40291.51944267, 27332.28858685, 27332.28858685, 27332.28858685])\n',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 1}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
