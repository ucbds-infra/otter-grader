OK_FORMAT = True

test = {   'name': 'q3_1',
    'points': None,
    'suites': [   {   'cases': [   {   'code': '>>> my_X = defaults[my_labels]\n'
                                               '>>> my_model = sm.OLS(Y, sm.add_constant(my_X))\n'
                                               '>>> my_result = my_model.fit()\n'
                                               '>>> my_Y_hat = my_result.fittedvalues\n'
                                               '>>> assert rmse(Y, my_Y_hat) <= 50000\n',
                                       'hidden': True,
                                       'locked': False}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
