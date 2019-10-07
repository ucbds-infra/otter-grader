import unittest
from local_grader.metadata import GradescopeParser, CanvasParser, JSONParser, YAMLParser

class TestGradescopeParser(unittest.TestCase):
	def setUp(self):
		self._path = "test/sample-metadata/gradescope-export"
		self._correct_result = [{
			"identifier": "12345",
			"filename": "file1.pdf"
		}, {
			"identifier": "23456",
			"filename": "file2.pdf"
		}, {
			"identifier": "someName",
			"filename": "odd_filename--s2034.ipynb"
		}, {
			"identifier": "someName",
			"filename": "GROUPodd_filename--s2034.ipynb"
		}, {
			"identifier": "someOtherName",
			"filename": "GROUPodd_filename--s2034.ipynb"
		}, {
			"identifier": "someOtherOtherName",
			"filename": "GROUPodd_filename--s2034.ipynb"
		}]

	def test_metadata(self):
		parser = GradescopeParser(self._path)
		self.assertEqual(parser.get_metadata(), self._correct_result)

class TestCanvasParser(unittest.TestCase):
	def setUp(self):
		self._path = "test/sample-metadata/canvas-export"
		self._correct_result = [{
			"identifier": "odd",
			"filename": "odd_filename--s2034.ipynb"
		}, {
			"identifier": "johndoe",
			"filename": "johndoe_LATE_5362839_74575800_markdown-intro (1).ipynb"
		}]

	def test_metadata(self):
		parser = CanvasParser(self._path)
		self.assertEqual(parser.get_metadata(), self._correct_result)

class TestJSONParser(unittest.TestCase):
	def setUp(self):
		self._path = "test/sample-metadata/test-metadata.json"
		self._correct_result = [{
			"identifier": "12345",
			"filename": "file1.pdf"
		}, {
			"identifier": "23456",
			"filename": "file2.pdf"
		}, {
			"identifier": "someName",
			"filename": "odd_filename--s2034.ipynb"
		}]

	def test_metadata(self):
		parser = JSONParser(self._path)
		self.assertEqual(parser.get_metadata(), self._correct_result)

class TestYAMLParser(unittest.TestCase):
	def setUp(self):
		self._path = "test/sample-metadata/test-metadata.yml"
		self._correct_result = [{
			"identifier": "12345",
			"filename": "file1.pdf"
		}, {
			"identifier": "23456",
			"filename": "file2.pdf"
		}, {
			"identifier": "someName",
			"filename": "odd_filename--s2034.ipynb"
		}]

	def test_metadata(self):
		parser = YAMLParser(self._path)
		self.assertEqual(parser.get_metadata(), self._correct_result)

if __name__ == "__main__":
	unittest.main()