import os
from concurrent.futures import ThreadPoolExecutor
import argparse
import csv
import ast
import logging
import time
from capture_socket import CaptureSocket
from auxclock import AuxClock
from domain import Domain

OUTPUT_DIR = 'output'
options = {'only_screenshot': False, 'target_time': 15, 'debug': 0, 'NS': ["8.8.8.8", "4.4.4.4"]}

def process_url(id, main_domain, domain_url):

    domain = Domain(id, main_domain, domain_url, options["NS"])
    try:
      if not options['only_screenshot']:
        domain.get_dns_info()
        if domain.a_info is not None or domain.cname_info is not None:
          domain.get_ssl_certificate()
          domain.get_whois_info()
          domain.get_mx_records()
          domain.take_screenshot()
      else:
         domain.take_screenshot()

    except Exception as e:
      print(f'[PROCESS_URL] {domain_url}: {str(e)}')
      domain.dump()
      
    del domain

#global clock for time measurement purposes
g_clock = AuxClock()

def main(input_csv, output_csv, num_threads):
    print("STARTED")
    g_clock.checkpoint('START')
    urls = []
    with open(input_csv, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        if options['debug'] > 0: 
            for i in range(options['debug']): #this loop skips until line N to avoid wasting time when debugging
                next(reader)
        for row in reader:
            id, main_domain, correlated_domains_json = row
            correlated_domains = ast.literal_eval(correlated_domains_json)
            for url in set(correlated_domains):
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

    i=0
    dots = "............................................"
    server = CaptureSocket()
    while(not server.terminate()):
      print("Waiting for screenshoter to end {}".format(dots[0:i % len(dots)]))
      i += 1
      time.sleep(5)
    
    print("Finished.")
    print("Thank you for using screenshoter")
    print("Allan Brunstein")
    print("Politecnico di Torino, 2023")
    print("Universidade de Sao Paulo, 2023")

      

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web information fetcher')
    parser.add_argument('--input', type=str, nargs='?', const='input.csv', default='input.csv', help='Input CSV file containing URLs (default: input.csv)')
    parser.add_argument('--output', type=str, nargs='?', const='output.csv', default='output.csv', help='Output CSV file to store results (default: output.csv)')
    parser.add_argument('--threads', type=int, nargs='?', const=4, default=4, help='Number of threads to use (default: 10)')
    parser.add_argument('--screenshot_only', type=int, nargs='?', const=False, default=False, help='If True, the program will only take a screenshot of the websites')
    parser.add_argument('--debug', type=int, nargs='?', const=0, default=0, help='Set domain to debug')
    parser.add_argument('--ns1', type=str, nargs='?', const="8.8.8.8", default="8.8.8.8", help='Nameserver 1 for DNS')
    parser.add_argument('--ns2', type=str, nargs='?', const="4.4.4.4", default="4.4.4.4", help='Nameserver 2 for DNS')
    parser.add_argument('--localhost', type=str, nargs='?', const="127.0.0.1", default="127.0.0.1", help='Socket address for .NET screenshoter')
    parser.add_argument('--localport', type=str, nargs='?', const="9018", default="9018", help='Port for screenshoter')

    args, _ = parser.parse_known_args()
    options['screenshot_only'] = args.screenshot_only
    options['debug'] = args.debug
    options['NS'] = [args.ns1,args.ns2]

    CaptureSocket.host = str(args.localhost)
    CaptureSocket.port = int(args.localport) 
    print("Wait 30 seconds for sockets to start")
    time.sleep(30) # sockets should open first

    logging.basicConfig(filename='log.log', level = logging.INFO)

    main(args.input, args.output, args.threads)