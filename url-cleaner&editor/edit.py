with open('domains.txt') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    parts = line.split('&')
    new_parts = []
    for part in parts:
        sub_parts = part.split('=')
        new_part = '='.join(sub_parts[:-1]) + '=[t]'
        new_parts.append(new_part)
    new_line = '&'.join(new_parts)
    new_lines.append(new_line + '\n')

with open('domains_edited.txt', 'w') as f:
    for line in new_lines:
        f.write(line)