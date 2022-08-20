from otter.test_files import test_case

OK_FORMAT = False

name = "q8"
points = None

@test_case(points=None, hidden=False)
def test_len(z):
    assert len(z) == 10

