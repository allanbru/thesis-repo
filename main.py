import os
from time import time
from concurrent.futures import ThreadPoolExecutor
import argparse
import csv
import ast
from datetime import datetime
import logging
from .auxclock import AuxClock
from .webbrowser import BrowserManager
from .domain import Domain

OUTPUT_DIR = 'output'
options = {'only_screenshot': False, 'target_time': 10, 'debug': 0}

def get_time_string():
    now = datetime.now()
    return now.strftime('%Y-%m-%d-%H-%M-%S')

def process_url(id, main_domain, domain_url):

    print(f'({id}) Starting: {domain_url}')
    domain = Domain(id, main_domain, domain_url)
    try:
      if not options['only_screenshot']:
        domain.get_ssl_certificate()
        domain.get_dns_info()
        domain.get_mx_records()
        domain.get_whois_info()
      domain.take_screenshot()

    except Exception as e:
      print(f'[PROCESS_URL] {domain_url}: {str(e)}')
      domain.dump()

    print(f'{id} Finished: {domain_url}')

#global clock for time measurement purposes
g_clock = AuxClock()

def main(input_csv, output_csv, num_threads):

    g_clock.checkpoint('START')
    urls = []
    _ = BrowserManager(num_threads, options['target_time'])

    with open(input_csv, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        if options['debug'] > 0: 
            for i in range(options['debug']): #this loop skips until line N to avoid wasting time
                next(reader)
        for row in reader:
            id, main_domain, correlated_domains_json = row
            correlated_domains = ast.literal_eval(correlated_domains_json)
            for url in set(correlated_domains):
                print(url)
                id = len(urls)
                urls.append((id, main_domain, url))
            g_clock.checkpoint(f'READ_MAIN_DOMAIN_{id}')
            
            if options['debug']:
                break # to debug only one domain

    if not os.path.exists('screenshots'):
      os.makedirs('screenshots')

    if not os.path.exists(OUTPUT_DIR):
      os.makedirs(OUTPUT_DIR)

    g_clock.checkpoint('START_EXEC')
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
      executor.map(lambda x: process_url(*x), urls)

    g_clock.checkpoint('END_EXEC')
    g_clock.end()

    n_domains = len(urls)
    clock_info = g_clock.dump()
    total_time = clock_info['end_time']
    rate = n_domains / total_time * 60.0

    print(f'Processed {n_domains} domains in {total_time} seconds')
    print(f'Average rate of {rate} domains/minute')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web information fetcher')
    parser.add_argument('--input', type=str, nargs='?', const='input.csv', default='input.csv', help='Input CSV file containing URLs (default: input.csv)')
    parser.add_argument('--output', type=str, nargs='?', const='output.csv', default='output.csv', help='Output CSV file to store results (default: output.csv)')
    parser.add_argument('--threads', type=int, nargs='?', const=4, default=4, help='Number of threads to use (default: 10)')
    parser.add_argument('--screenshot_only', type=int, nargs='?', const=False, default=False, help='If True, the program will only take a screenshot of the websites')
    parser.add_argument('--debug', type=int, nargs='?', const=0, default=0, help='Set domain to debug')
    args, _ = parser.parse_known_args()
    options['screenshot_only'] = args.screenshot_only
    options['debug'] = args.debug

    logging.basicConfig(filename='log.log', level = logging.INFO)

    main(args.input, args.output, args.threads)