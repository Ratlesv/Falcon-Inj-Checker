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
import httpx
import urllib3
from logging.handlers import RotatingFileHandler
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from requests.exceptions import ProxyError
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectorError, ClientProxyConnectionError, ServerTimeoutError
from tqdm import tqdm

# Import the necessary utilities from utils.py
from utils import setup_logging, print_banner, update_statistics, update_stats_periodically, handle_request_errors, user_agent_cycle, SQLInjectionChecker, read_proxies, load_urls, process_urls, save_results ,check_file_path ,check_positive_float

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

init(autoreset=False)  # Initialize colorama without auto-reset

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
