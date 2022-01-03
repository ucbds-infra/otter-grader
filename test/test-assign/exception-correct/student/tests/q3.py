from otter.test_files import test_case

OK_FORMAT = False

name = "q3"
points = None

@test_case(points=None, hidden=False)
def test_public(nine, square):
    assert nine == 9
    assert square(16) == 256

