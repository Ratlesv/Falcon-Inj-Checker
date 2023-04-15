import os
import re

def split_file(filename, lines_per_file):
    with open(filename, 'r') as infile:
        lines = infile.readlines()
    file_count = 0
    for i in range(0, len(lines), lines_per_file):
        with open(f'{filename}_{file_count}.txt', 'w') as outfile:
            outfile.writelines(lines[i:i+lines_per_file])
            file_count += 1
    os.remove(filename)

no_file = 'no.txt_0'
with open(no_file, 'r') as f:
    # extract the integer value from the first line of the file
    first_line = f.readline()
    num_lines = int(re.search(r'\d+', first_line).group())

split_file('no.txt_0', 10000)
