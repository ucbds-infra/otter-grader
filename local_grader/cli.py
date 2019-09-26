import argparse
import pandas as pd
import os

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-g", "--gradescope", action="store_true")
	parser.add_argument("-c", "--canvas", action="store_true")
	parser.add_argument("-j", "--json", nargs="?", default="student_data.json", action="store_true")
	parser.add_argument("-y", "--yaml", nargs="?", default="student_data.json", action="store_true")
	parser.add_argument("-n", "--notebooks-path",  type=str, default="/")
	parser.add_argument("-t", "--tests-path", type=str, default="/tests/")
	parser.add_argument("-o", "--output-path", type=str, default="/")
	parser.add_argument("-v", "--verbose", action="store_true")
	parser.add_argument("-cf", "--custom-file", default="/")
	params = vars(parser.parse_args())
	
	# Default Custom Files for json/yaml metadata
	# if params["custom-file"] == "/":
	# 	if params["json"]:
	# 		params["custom-file"] = "student_data.json"
	# 	elif params["yaml"]:
	# 		params["custom-file"] = "student_data.yaml"

	# Asserts that exactly one metadata flag is provided
	assert sum([params["gradescope"], \
					params["canvas"], \
					params["json"], \
					params["yaml"]]) == 1, \
				"You must supply exactly one metadata flag (-g, -j, -y, -c)"

# Exports a list of dataframes as a single, merged csv file
def merge_export_csv(dataframes, output_path):
	original_directory = os.getcwd()
	os.chdir(output_path)
	final_dataframe = pd.concat(dataframes, axis=1, join='inner').sort_index()
	final_dataframe.to_csv("final_grades.csv")
	os.chdir(original_directory)

if __name__ == "__main__":
	main()
