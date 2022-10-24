OK_FORMAT = True

test = {   'name': 'q1_7',
    'points': None,
    'suites': [   {   'cases': [   {   'code': '>>> np.random.seed(1234)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y_hat2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(rmse(y2, y_hat2), 2.440102731334708)\n',
                                       'hidden': False,
                                       'locked': False},
                                   {   'code': '>>> np.random.seed(2345)\n'
                                               '>>> y2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> y_hat2 = np.random.uniform(0, 10, 5)\n'
                                               '>>> assert np.isclose(rmse(y2, y_hat2), 4.034226624125118)\n',
                                       'hidden': True,
                                       'locked': False,
                                       'points': 1}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
