import requests
import re
import sys
import argparse
from itertools import cycle
import urllib3
from concurrent.futures import ThreadPoolExecutor
import time
import random
from colorama import init, Fore

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

init(autoreset=False)  # Initialize colorama without auto-reset


class SQLInjectionChecker:

    def __init__(self, proxy_list, timeout=10, payloads_file="payloads.txt", sql_patterns_file="sql-patterns.txt"):
        self.proxies = proxy_list
        self.timeout = timeout
        self.proxy_cycle = cycle(proxy_list)
        
        with open(payloads_file, "r") as f:
            self.payloads = [line.strip() for line in f.readlines()]

        with open(sql_patterns_file, "r") as f:
            self.sql_errors = [line.strip() for line in f.readlines()]

    def get_next_proxy(self):
        return next(self.proxy_cycle)

    def check_sql_injection(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        try:
            for payload in self.payloads:
                injected_url = url.replace("[t]", payload)
                proxy = self.get_next_proxy()
                response = requests.get(injected_url, proxies={"http": proxy, "https": proxy}, headers=headers, timeout=self.timeout, verify=False)

                for error in self.sql_errors:
                    if re.search(error, response.text, re.IGNORECASE):
                        return True
        except requests.exceptions.RequestException as e:
            print(f"Error while sending request to {url}: {e}")

        return False


def check_url(url, checker):
    time.sleep(random.uniform(args.min_delay, args.max_delay))  # Add a random delay between requests
    if checker.check_sql_injection(url):
        print(f"{url} might be SQL injectable.")
        return url
    else:
        print(f"{url} seems not to be SQL injectable.")
        return None


def main(args):
    print("Made With Love By Th3 Gr34T F4LC0N")
    input("Press Enter to start checking URLs...")

    proxy_list = args.proxies.split(',')

    checker = SQLInjectionChecker(proxy_list, args.timeout)

    with open(args.urls, "r", encoding="utf-8") as f:
        urls = f.readlines()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        results = list(executor.map(lambda url: check_url(url.strip(), checker), urls))

    results = [result for result in results if result is not None]

    with open(args.output, "w") as f:
        for result in results:
            f.write(f"{result}\n")

    # Add a report at the end with the number of working URLs in green color
    print(Fore.GREEN + f"Number of Working URLs: {len(results)}" + Fore.RESET)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQL Injection Checker")
    parser.add_argument("--urls", type=str, default="urls.txt", help="Path to the file containing URLs")
    parser.add_argument("--proxies", type=str, default="http://127.0.0.1:24000,http://127.0.0.1:24001,http://127.0.0.1:24002", help="Comma-separated list of proxies")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--output", type=str, default="result.txt", help="Output file for saving SQL injectable URLs")
    parser.add_argument("--threads", type=int, default=5, help="Number of concurrent threads")
    parser.add_argument("--min_delay", type=float, default=1.0, help="Minimum delay between requests in seconds")
    parser.add_argument("--max_delay", type=float, default=3.0, help="Maximum delay between requests in seconds")

    args = parser.parse_args()
    main(args)

