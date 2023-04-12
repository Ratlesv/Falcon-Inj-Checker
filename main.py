import argparse
import asyncio
import aiohttp
import curses
import itertools
import os
import sys
import random
import time
import re
import threading
import traceback
import logging
import logging.config
import requests
import urllib3
from logging.handlers import RotatingFileHandler
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from requests.exceptions import ProxyError
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectorError, ClientProxyConnectionError, ServerTimeoutError
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

init(autoreset=False)  # Initialize colorama without auto-reset

def setup_logging():
    config = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
            },
            "file": {
                "()": RotatingFileHandler,  # Use custom handler class
                "filename": "logfile.log",
                "formatter": "default",
                "level": "INFO",
                "maxBytes": 10 * 1024 * 1024,  # Set max file size to 10 MB
                "backupCount": 3,  # Keep up to 3 backup files
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
            }
        },
    }

    logging.config.dictConfig(config)
    
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

def update_statistics(stdscr, current_url, proxies, processed_urls, total_urls, injectable_count, start_time):
    elapsed_time = time.time() - start_time
    elapsed_minutes, elapsed_seconds = divmod(elapsed_time, 60)

    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(7, 0, "**********************************")
    stdscr.attroff(curses.color_pair(2))
    stdscr.addstr(8, 0, f"Current URL: {current_url}")
    stdscr.addstr(9, 0, "")  # Add an empty line for spacing
    stdscr.addstr(10, 0, "")  # Add an empty line for spacing
    stdscr.addstr(11, 0, "")  # Add an empty line for spacing
    stdscr.addstr(12, 0, "")  # Add an empty line for spacing
    stdscr.addstr(13, 0, "")  # Add an empty line for spacing
    stdscr.addstr(14, 0, "")  # Add an empty line for spacing
    stdscr.addstr(15, 0, "")  # Add an empty line for spacing
    stdscr.addstr(16, 0, "")  # Add an empty line for spacing
    stdscr.addstr(17, 0, "")  # Add an empty line for spacing
    stdscr.addstr(18, 0, "")  # Add an empty line for spacing
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(19, 0, "**********************************")
    stdscr.attroff(curses.color_pair(2))    
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(20, 0, f"Processed URLs: {processed_urls}/{total_urls}")
    stdscr.attroff(curses.color_pair(1))
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(21, 0, f"Injectable URLs Found: {injectable_count}")
    stdscr.attroff(curses.color_pair(1))
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(22, 0, f"Elapsed Time: {int(elapsed_minutes):02d}:{int(elapsed_seconds):02d}")
    stdscr.attroff(curses.color_pair(1))
    stdscr.refresh()

def update_stats_periodically(stdscr, checker, delay=2):
    while True:
        time.sleep(delay)
        update_statistics(stdscr, checker.current_url, checker.proxies, checker.processed_urls, checker.total_urls, checker.injectable_count, checker.start_time)

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

def user_agent_cycle():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]
    return cycle(user_agents)

class SQLInjectionChecker:
    def __init__(self, proxy_list, timeout=10, payloads_file="payloads.txt", sql_patterns_file="sql-patterns.txt"):
        self.proxies = proxy_list
        self.timeout = timeout
        self.user_agents = user_agent_cycle()
        self.payloads = self._read_file(payloads_file)
        self.sql_errors = self._read_file(sql_patterns_file)
        self.current_url = ""
        self.processed_urls = 0
        self.total_urls = 0
        self.injectable_count = 0
        self.start_time = time.time()
        self.proxy_generator = self.proxy_cycle()

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

    def proxy_cycle(self):
        return cycle(self.proxies)

    def check_sql_injection(self, url, retries=3):
        for _ in range(retries):
            for payload in self.payloads:
                injected_url = url.replace("[t]", payload)
                proxy = next(self.proxy_generator)

                print(f"Using proxy: {proxy} for URL: {injected_url}")

                # Rotate the User-Agent for each request
                headers = {
                    "User-Agent": next(self.user_agents),
                }

                response = self.request_injected_url(injected_url, proxy, headers)

                if response is not None:
                    for error in self.sql_errors:
                        if re.search(error, response.text, re.IGNORECASE):
                            return True

        return False

def check_url(url, checker, stdscr, min_delay, max_delay, output_file):
    logging.info(f"Processing URL: {url}")
    is_injectable = None

    try:
        time.sleep(random.uniform(min_delay, max_delay))
        is_injectable = checker.check_sql_injection(url)
        checker.current_url = url
        checker.processed_urls += 1
        if is_injectable:
            checker.injectable_count += 1
            with open(output_file, "a") as f:
                f.write(f"{url}\n")
            logging.info(f"Injectable URL found: {url}")
    except Exception as e:
        logging.error(f"Error processing URL {url}: {e}")

    update_statistics(stdscr, url, checker.proxies, checker.processed_urls, checker.total_urls, checker.injectable_count, checker.start_time)
    return url if is_injectable else None

def read_proxies(proxy_file):
    return SQLInjectionChecker._read_file(proxy_file)


def load_urls(file_path):
    return SQLInjectionChecker._read_file(file_path)


def process_urls(urls, checker, stdscr, args):
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(lambda url: check_url(url, checker, stdscr, args.min_delay, args.max_delay, args.output), url) for url in urls]

        with tqdm(total=len(futures), bar_format="{percentage:3.0f}%|{bar}| {n}/{total}", file=sys.stderr) as pbar:
            for future in as_completed(futures):
                try:
                    if future.exception() is not None:
                        logging.error(f"Error processing URL: {future.exception()}")
                    elif future.result() is not None:
                        pbar.update(1)
                except Exception:
                    logging.exception(f"Error processing URL {url}")

        return [future.result() for future in futures if future.result() is not None]
def save_results(results, output_file):
    try:
        with open(output_file, "w") as f:
            for result in results:
                f.write(f"{result}\n")
    except IOError as e:
        print(f"Error writing to the output file: {e}")
        sys.exit(1)

def check_file_path(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"{path} is not a valid file path")
    return path

def check_positive_float(value):
    try:
        f_value = float(value)
        if f_value <= 0:
            raise argparse.ArgumentTypeError(f"{value} must be a positive float")
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid float")
    return f_value

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

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(6, 0, "Threads: ")
    stdscr.attroff(curses.color_pair(1))

    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(6, 9, str(args.threads))
    stdscr.attroff(curses.color_pair(2))

    stdscr.refresh()

    checker = SQLInjectionChecker(proxy_list)
    checker.total_urls = len(urls)
    update_statistics(stdscr, checker.current_url, proxy_list, checker.processed_urls, checker.total_urls, checker.injectable_count, checker.start_time)

    # Start the stats update thread
    stats_thread = threading.Thread(target=update_stats_periodically, args=(stdscr, checker))
    stats_thread.daemon = True
    stats_thread.start()
    
    injectable_urls = process_urls(urls, checker, stdscr, args)

    save_results(injectable_urls, args.output)

if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="Th3-GR34T-F4LC0N URL INJ Checker")
    parser.add_argument("-p", "--proxies", required=True, type=check_file_path, help="Path to the proxies file.")
    parser.add_argument("-u", "--urls", required=True, type=check_file_path, help="Path to the URLs file.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output file.")
    parser.add_argument("-t", "--threads", type=int, default=10, choices=range(1, 101), help="Number of threads (default: 10).")
    parser.add_argument("--min-delay", type=check_positive_float, default=0.5, help="Minimum delay between requests in seconds (default: 0.5).")
    parser.add_argument("--max-delay", type=check_positive_float, default=1.5, help="Maximum delay between requests in seconds (default: 1.5).")

    args = parser.parse_args()

    curses.wrapper(main, args)
