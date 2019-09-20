import os

def list_files(path):
	"""Returns list of all files in a directory, ignores hidden files"""
	assert os.path.isdir(path), "Provided path is not a directory"
	return [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file[0] != "."]