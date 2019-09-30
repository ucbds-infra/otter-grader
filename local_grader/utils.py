import os

def list_files(path):
	"""Returns a list of all non-hidden files in a directory"""
	return [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file[0] != "."]