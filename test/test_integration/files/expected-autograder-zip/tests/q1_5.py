OK_FORMAT = True

test = {   'name': 'q1_5',
    'points': None,
    'suites': [   {   'cases': [   {'code': '>>> assert 0.13 <= ci95_lower <= 0.17\n>>> assert 0.16 <= ci95_upper <= 0.20\n', 'hidden': False, 'locked': False},
                                   {'code': '>>> assert np.isclose(ci95_lower, 0.1442893482315043)\n', 'hidden': True, 'locked': False, 'points': 0.5},
                                   {'code': '>>> assert np.isclose(ci95_upper, 0.1863526283850078)\n', 'hidden': True, 'locked': False, 'points': 0.5}],
                      'scored': True,
                      'setup': '',
                      'teardown': '',
                      'type': 'doctest'}]}
