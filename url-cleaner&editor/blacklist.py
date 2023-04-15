with open('domains.txt', 'r') as f:
    domains = f.readlines()

with open('blacklist.txt', 'r') as f:
    blacklist = f.readlines()

blacklist = [x.strip() for x in blacklist]

clean_domains = []
for domain in domains:
    if not any(x in domain for x in blacklist):
        clean_domains.append(domain)

with open('clean_domains.txt', 'w') as f:
    f.writelines(clean_domains)
