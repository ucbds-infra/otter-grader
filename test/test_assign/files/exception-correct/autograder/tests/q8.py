from otter.test_files import test_case

OK_FORMAT = False

name = "q8"
points = None

@test_case(points=None, hidden=False)
def test_len(z):
    assert len(z) == 10

@test_case(points=None, hidden=True)
def test_values(np, z):
    assert np.allclose(z, [4.99342831, 3.7234714, 5.29537708, 7.04605971, 3.53169325, 3.53172609, 7.15842563, 5.53486946, 3.06105123, 5.08512009])

