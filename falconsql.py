#!/usr/bin/env python3
import requests
import re
import sys
import argparse
import os
from itertools import cycle
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from colorama import init, Fore
from tqdm import tqdm
from requests.exceptions import ProxyError


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

                # Print the proxy being used for the current request
                print(f"Using proxy: {proxy} for URL: {injected_url}")

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
        tqdm.write(f"{url} might be SQL injectable.")
        return url
    else:
        tqdm.write(f"{url} seems not to be SQL injectable.")
        return None

def read_proxies(proxy_file):
    if not os.path.isfile(proxy_file):
        raise FileNotFoundError(f"{proxy_file} not found.")
    with open(proxy_file, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def main(args):
    print("Made With Love By Th3 Gr34T F4LC0N")
    input("Press Enter to start checking URLs...")

    proxy_list = read_proxies(args.proxies)

    checker = SQLInjectionChecker(proxy_list, args.timeout)

    with open(args.urls, "r", encoding="utf-8") as f:
        urls = f.readlines()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(lambda url: check_url(url.strip(), checker), url) for url in urls]

        # Use tqdm to create a progress bar
        with tqdm(total=len(futures)) as pbar:
            for future in as_completed(futures):
                # Update the progress bar after each completed task
                if future.result() is not None:
                    pbar.update(1)

    # Get the results from the futures
    results = [future.result() for future in futures if future.result() is not None]

    with open(args.output, "w") as f:
        for result in results:
            f.write(f"{result}\n")

    # Add a report at the end with the number of working URLs in green color
    print(Fore.GREEN + f"Number of Working URLs: {len(results)}" + Fore.RESET)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQL Injection Checker")
    parser.add_argument("--urls", type=str, default="urls.txt", help="Path to the file containing URLs")
    parser.add_argument("--proxies", type=str, default="proxies.txt", help="Path to the file containing proxies")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--output", type=str, default="result.txt", help="Output file for saving SQL injectable URLs")
    parser.add_argument("--threads", type=int, default=50, help="Number of concurrent threads")
    parser.add_argument("--min_delay", type=float, default=1.0, help="Minimum delay between requests in seconds")
    parser.add_argument("--max_delay", type=float, default=3.0, help="Maximum delay between requests in seconds")

    args = parser.parse_args()
    main(args)
