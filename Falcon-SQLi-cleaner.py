def has_equal_sign(line):
    return "=" in line

def process_links(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        unique_lines = set()

        for line in infile:
            line = line.strip()
            if has_equal_sign(line) and line not in unique_lines:
                unique_lines.add(line)
                outfile.write(line + '\n')

# Usage:
input_file = 'urls.txt'
output_file = 'clean_urls.txt'
process_links(input_file, output_file)
