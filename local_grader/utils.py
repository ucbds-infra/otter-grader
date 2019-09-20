import os

def list_files(path):
	return [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]