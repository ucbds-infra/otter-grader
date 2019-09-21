import argparse
import pandas as pd
import os

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-g", "--gradescope", action="store_true")
	parser.add_argument("-c", "--canvas", action="store_true")
	parser.add_argument("-j", "--json", action="store_true")
	parser.add_argument("-y", "--yaml", action="store_true")
	parser.add_argument("-n", "--notebooks-path",  type=str, default="/")
	parser.add_argument("-t", "--tests-path", type=str, default="/tests/")
	parser.add_argument("-o", "--output-path", type=str, default="/")
	parser.add_argument("-v", "--verbose", action="store_true")
	parser.add_argument("-cf", "--custom-file", default="/")
	params = vars(parser.parse_args())
	#TODO : Default custom file 

	# Asserts that exactly one metadata flag is provided
	assert sum([params["gradescope"], \
					params["canvas"], \
					params["json"], \
					params["yaml"]]) == 1, \
				"You must supply exactly one metadata flag (-g, -j, -y, -c)"

#TODO: incorporate for list of dfs
def merge_csv(csv_path, output_path):
	os.chdir(csv_path)
	dfs = [pd.read_csv(f, index_col=[0], parse_dates=[0])\
        for f in os.listdir(os.getcwd()) if f.endswith('csv')]
	finaldf = pd.concat(dfs, axis=1, join='inner').sort_index()

# Extract information such as path to files, tests
# CSV Merging (attempted)
# Replace underscore with hyphens (done)

if __name__ == "__main__":
	main()
