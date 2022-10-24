OK_FORMAT = True

test = {   'name': 'q2_3',
    'points': None,
    'suites': [   {   'cases': [   {'code': '>>> assert len(Y_hat) == defaults.shape[0]\n>>> assert 22000 <= multi_rmse <= 23000\n', 'hidden': False, 'locked': False},
                                   {   'code': '>>> np.random.seed(1234)\n'
                                               '>>> expected = np.array([131575.00462172,  26777.22647566,   2573.18036936,   2824.68190761, 50299.39627643])\n'
                                               '>>> actual = np.random.choice(Y_hat, 5)\n'
                                               '>>> assert np.allclose(expected, actual)\n',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 1},
                                   {'code': '>>> assert np.isclose(multi_rmse, 22561.189743524323)\n', 'hidden': True, 'locked': False, 'points': 1}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
