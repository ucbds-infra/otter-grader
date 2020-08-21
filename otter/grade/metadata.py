"""
Metadata parsers for Otter Grade
"""

import yaml
import json
import glob
import os
import re
import shutil

from .utils import list_files


FILENAME_REGEX = r"^.+\."


class GradescopeParser:
	"""Metadata parser for Gradescope exports

    Args:
        submissions_dir (``str``): path to directory with student submission files which contains 
			the ``submission_metadata.yml`` file
	"""

	def __init__(self, submissions_dir):
		# open metadata file and load into Python object
		with open(os.path.join(submissions_dir, "submission_metadata.yml")) as f:
			metadata = yaml.safe_load(f)

		# initialize metadata list
		self._metadata = []
		for folder in metadata:
			# copy submission contents into export root directory
			for file in os.listdir(os.path.join(submissions_dir, folder)):
				if os.path.isfile(os.path.join(submissions_dir, folder, file)) \
					and file[-6:] == ".ipynb":
					# create new filename
					new_filename = re.sub(FILENAME_REGEX, folder + ".", file)

					# ensure we are not overwriting another IPYNB file
					assert not os.path.exists(os.path.join(submissions_dir, folder + ".ipynb")), \
					"Extracting files from folder {} would overwrite another file in the\
					submissions directory.".format(folder)

					# copy the file
					shutil.copy(os.path.join(submissions_dir, folder, file), 
						os.path.join(submissions_dir, new_filename))

			# iterate through submitters for group submissions
			for submitter in metadata[folder][":submitters"]:
				self._metadata += [{

					# metadata is separated by filename into a list of submitters
					# and we use the name as the identifier
					"identifier": submitter[":name"],
					"filename": folder + ".ipynb"
				}]

		self._file_to_id = {file["filename"] : file["identifier"] for file in self._metadata}
		self._id_to_file = {file["identifier"] : file["filename"] for file in self._metadata}

	def get_metadata(self):
		"""Returns mapping of identifiers to files
		
		Returns:
			``list`` of ``dict``: list of dictionaries with identifier and filename information for 
				each submission
		"""
		return self._metadata

	def file_to_id(self, file):
		"""Returns a identifier given a filename
		
		Args:
			file (``str``): filename of a submission
		
		Returns:
			``str``: identifier corresponding to filename
		"""
		return self._file_to_id[file]

	def id_to_file(self, identifier):
		"""Returns a filename given an identifier
		
		Args:
			identifier (``str``): identifier of a submitter

		Returns:
			``str``: filename of that submitter's submission
		"""
		return self._id_to_file[identifier]

	def get_identifiers(self):
		"""Returns list of submission identifiers
		
		Returns:
			``list``: all identifiers from this parser
		"""
		return [file["identifier"] for file in self._metadata]

	def get_filenames(self):
		"""Returns list of filenames in the submission directory
		
		Returns:
			``list``: all filenames from this parser
		"""
		return [file["filename"] for file in self._metadata]

	def get_folders(self):
		"""Returns a list of the submission folder names from this parser

		Returns:
			``list``: the folder basenames
		"""
		return list(self._metadata.keys())


class CanvasParser:
	"""Metadata parser for Canvas exports
	
	Args:
        submissions_dir (``str``): path to directory with student submission files
	"""
	def __init__(self, submissions_dir):
		# list all files in the submissions directory since Canvas
		# doesn't output a metadata file
		submissions = list_files(submissions_dir)

		# intialize metadata list and iterate through the files
		self._metadata = []
		for file in submissions:
			# extract the identifier from the filename, which is everything
			# before the first underscore, meaning
			# somestudent_12345_67890_SomeStudent.ipynb -> somestudent
			identifier = re.match(r"(\w+?)\_", file)[1]

			# add the identifier and filename to the metadata list
			self._metadata += [{
				"identifier": identifier,
				"filename": file
			}]

		self._file_to_id = {file["filename"] : file["identifier"] for file in self._metadata}
		self._id_to_file = {file["identifier"] : file["filename"] for file in self._metadata}

	def get_metadata(self):
		"""Returns mapping of identifiers to files
		
		Returns:
			``list`` of ``dict``: list of dictionaries with identifier and filename information for 
				each submission
		"""
		return self._metadata

	def file_to_id(self, file):
		"""Returns a identifier given a filename
		
		Args:
			file (``str``): filename of a submission
		
		Returns:
			``str``: identifier corresponding to filename
		"""
		return self._file_to_id[file]

	def id_to_file(self, identifier):
		"""Returns a filename given an identifier
		
		Args:
			identifier (``str``): identifier of a submitter

		Returns:
			``str``: filename of that submitter's submission
		"""
		return self._id_to_file[identifier]

	def get_identifiers(self):
		"""Returns list of submission identifiers
		
		Returns:
			``list``: all identifiers from this parser
		"""
		return [file["identifier"] for file in self._metadata]

	def get_filenames(self):
		"""Returns list of filenames in the submission directory
		
		Returns:
			``list``: all filenames from this parser
		"""
		return [file["filename"] for file in self._metadata]


class JSONParser:
	"""Metadata parser for JSON format
	
	Args:
        file_path (``str``): path to JSON metadata file
	
	"""
	def __init__(self, file_path):
		# open JSON file and load contents into a string
		with open(file_path) as f:
			metdata = f.read()

		# parse string with json library
		self._metadata = json.loads(metdata, parse_int=str)

		# check that the JSON file has the correct structure
		assert type(self._metadata) == list, "JSON metadata is not a list"
		
		# check that each item in the JSON file is of correct type
		# and has "identifier" and "filename" keys
		for file in self._metadata:
			assert type(file) == dict, "JSON metadata does not have dictionaries"
			assert "identifier" in file.keys(), "JSON metadata does not contain \"identifier\" key"
			assert "filename" in file.keys(), "JSON metadata does not contain \"filename\" key"

		self._file_to_id = {file["filename"] : file["identifier"] for file in self._metadata}
		self._id_to_file = {file["identifier"] : file["filename"] for file in self._metadata}

	def get_metadata(self):
		"""Returns mapping of identifiers to files
		
		Returns:
			``list`` of ``dict``: list of dictionaries with identifier and filename information for 
				each submission
		"""
		return self._metadata

	def file_to_id(self, file):
		"""Returns a identifier given a filename
		
		Args:
			file (``str``): filename of a submission
		
		Returns:
			``str``: identifier corresponding to filename
		"""
		return self._file_to_id[file]

	def id_to_file(self, identifier):
		"""Returns a filename given an identifier
		
		Args:
			identifier (``str``): identifier of a submitter

		Returns:
			``str``: filename of that submitter's submission
		"""
		return self._id_to_file[identifier]

	def get_identifiers(self):
		"""Returns list of submission identifiers
		
		Returns:
			``list``: all identifiers from this parser
		"""
		return [file["identifier"] for file in self._metadata]

	def get_filenames(self):
		"""Returns list of filenames in the submission directory
		
		Returns:
			``list``: all filenames from this parser
		"""
		return [file["filename"] for file in self._metadata]


class YAMLParser:
	"""Metadata parser for YAML format
	
	Args:
        file_path (``str``): path to YAML metadata file
	"""
	def __init__(self, file_path):
		# open the YAML file and parse with yaml library
		with open(file_path) as f:
			self._metadata = yaml.safe_load(f)

		# convert any integer identifiers to strings
		for file in self._metadata:
			file["identifier"] = str(file["identifier"])

		# check that the YAML file has the correct structure
		assert type(self._metadata) == list, "YAML metadata is not a list"
		
		# check that each item in the YAML file is of correct type
		# and as "identifier" and "filename" keys
		for file in self._metadata:
			assert type(file) == dict, "YAML metadata does not have dictionaries"
			assert "identifier" in file.keys(), "YAML metadata does not contain \"identifier\" key"
			assert "filename" in file.keys(), "YAML metadata does not contain \"filename\" key"

		self._file_to_id = {file["filename"] : file["identifier"] for file in self._metadata}
		self._id_to_file = {file["identifier"] : file["filename"] for file in self._metadata}

	def get_metadata(self):
		"""Returns mapping of identifiers to files
		
		Returns:
			``list`` of ``dict``: list of dictionaries with identifier and filename information for 
				each submission
		"""
		return self._metadata

	def file_to_id(self, file):
		"""Returns a identifier given a filename
		
		Args:
			file (``str``): filename of a submission
		
		Returns:
			``str``: identifier corresponding to filename
		"""
		return self._file_to_id[file]

	def id_to_file(self, identifier):
		"""Returns a filename given an identifier
		
		Args:
			identifier (``str``): identifier of a submitter

		Returns:
			``str``: filename of that submitter's submission
		"""
		return self._id_to_file[identifier]

	def get_identifiers(self):
		"""Returns list of submission identifiers
		
		Returns:
			``list``: all identifiers from this parser
		"""
		return [file["identifier"] for file in self._metadata]

	def get_filenames(self):
		"""Returns list of filenames in the submission directory
		
		Returns:
			``list``: all filenames from this parser
		"""
		return [file["filename"] for file in self._metadata]
