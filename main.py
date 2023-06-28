import os
import ssl
import socket
from time import sleep, time
import tldextract
import whois
import dns.resolver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
import argparse
import csv
import ast
import multiprocessing
from datetime import datetime
import ndjson
import asyncio
import logging
import json

DEBUG_NONE, DEBUG_WRITE, DEBUG_PRINT = range(3)

OUTPUT_DIR = 'output'
options = {'only_screenshot': False, 'target_time': 10}

def get_time_string():
    now = datetime.now()
    return now.strftime('%Y-%m-%d-%H-%M-%S')

# Defining exception if function takes too long
class TimeLimitException(Exception):
    pass

def call_timeout(timeout, func, args=(), kwargs={}):
    if type(timeout) not in [int, float] or timeout <= 0.0:
      print("Invalid timeout!")

    elif not callable(func):
      print("{} is not callable!".format(type(func)))

    else:
      p = multiprocessing.Process(target=func, args=args, kwargs=kwargs)
      p.start()
      p.join(timeout)

      if p.is_alive():
        p.terminate()
        raise TimeLimitException(f'Took to long to execute {str(func)}({str(args)})')
        return False
      else:
        return True

# Clock to measure execution time
class AuxClock():

  def __init__(self):
    self.active = True
    self.init_time = time()
    self.checkpoints = {}
    self.end_time = None

  # Creates a checkpoint with the given name, return time since init_time
  def checkpoint(self, name):
    checkpoint_time = time()
    self.checkpoints[str(name)] = checkpoint_time
    return checkpoint_time - self.init_time

  # Finalizes the clock, return time of execution
  def end(self):
    self.end_time = time()
    return self.end_time - self.init_time

  def dump(self):
    dump_dict = {}
    for key, timestamp in self.checkpoints.items():
      dump_dict[key] = float(timestamp - self.init_time)
    dump_dict['end_time'] = float(self.end_time - self.init_time)
    return dump_dict

class WebBrowser:

  manager = None
  NEXT_BROWSER_ID = 0

  def __init__(self, manager = None):
    self.id = self.NEXT_BROWSER_ID
    self.init_browser()
    self.init_task_time = time()
    self.domain_instance = None
    WebBrowser.manager = manager
    WebBrowser.NEXT_BROWSER_ID += 1

  def init_browser(self):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    self.browser = webdriver.Chrome(options=chrome_options)
    self.free = True

  def take_screenshot(self, url, file_path, instance = None):
    self.init_task_time = time()
    if self.free:
      self.free = False
      status = False
      try:
        status = call_timeout(options['target_time'], self.internal_take_screenshot, args=(url, file_path))
      except TimeLimitException as e:
        print(f"[BROWSER] Timed out!")
      status = self.internal_take_screenshot(url, file_path)
      if status and isinstance(self.manager, BrowserManager):
        self.free = True
        self.manager.free_callback(self)
      else:
        self.interrupt()

      return status
    else:
      raise Exception(f'[BROWSER {self.id}] {url}: take_screenshot called when busy')

  def internal_take_screenshot(self, url, file_path):

    if self.browser is None:
      self.init_browser()
    try:
      self.browser.get(f'https://{url}')
      self.browser.save_screenshot(file_path)
      #close?
      print(f'[BROWSER {self.id}] Screenshot taken for {url}. Location: {file_path}')
      return True
    except Exception as e:
      print(f'[BROWSER {self.id}] Got an error while taking the screenshot for {url}: {str(e)}')
      if isinstance(self.domain_instance, Domain):
        self.domain_instance.screenshot_callback(False, '')
      return False

    return False

  def interrupt(self):
    print(f'[BROWSER {self.id}] INTERRUPTING AND RESTARTING')
    self.manager = BrowserManager()
    del(self.browser)
    self.init_browser()
    self.init_task_time = time()
    self.manager.free_callback(self)

class BrowserManager:

  queue = []
  num_instances = 1
  instances = []
  free_instances = set()

  def __init__(self, num_instances = -1):
    if num_instances == -1:
      num_instances = BrowserManager.num_instances
    BrowserManager.num_instances = num_instances
    while len(BrowserManager.instances) < num_instances:
        print(f'[BROWSERMANAGER] CREATING NEW INSTANCE. NUM_INSTANCES = {len(BrowserManager.instances) + 1}/{BrowserManager.num_instances}')
        browser = WebBrowser(self)
        BrowserManager.instances.append(browser)
        BrowserManager.free_instances.add(browser)

  # Check if there is a free web browser and a site to process
  @classmethod
  def checkQueue(cls):
    print(f'Checking queue: {len(cls.queue)} sites waiting. {len(cls.free_instances)} browsers vacant.')
    if len(cls.free_instances) > 0 and len(cls.queue) > 0:
      browser = cls.free_instances.pop()
      domain = cls.pop_domain()
      if domain is not None:
        (url, file_path, instance) = domain
        instance.clock.checkpoint('SCREENSHOT_DEQUEUED')
        print(f'[MANAGER] BROWSER {browser.id} is now BUSY')
        status = browser.take_screenshot(url, file_path, instance)
        instance.screenshot_callback(status, file_path)
    cls.checkForCrashes()


  @classmethod
  def checkForCrashes(cls):
    for i, browser in enumerate(cls.instances):
      time_executing = time() - browser.init_task_time
      if not browser.free and time_executing >= options['target_time']:
        browser.interrupt()
    cls.checkQueue()


  # Called from the Domain to insert a website on the list
  @classmethod
  def push(cls, url, file_path, instance):
    cls.queue.append((url, file_path, instance))
    instance.clock.checkpoint('SCREENSHOT_QUEUED')
    cls.checkQueue()

  # Get the next domain to process, internal call
  @classmethod
  def pop_domain(cls):
    if len(cls.queue) > 0:
      return cls.queue.pop(0)
    return None

  # WebBrowser calls when free
  @classmethod
  def free_callback(cls, browser):
    if isinstance(browser, WebBrowser):
      cls.free_instances.add(browser)
      print(f'[MANAGER] BROWSER {browser.id} is now FREE')
      cls.checkQueue()


class Domain:

  manager = None

  def __init__(self, id, main_domain, url):
    self.id = id
    self.clock = AuxClock()
    self.main_domain = main_domain
    ext = tldextract.extract(url)
    self.domain = f'{ext.domain}.{ext.suffix}'
    self.ssl_cert = None
    self.dns_info = None
    self.mx_info = None
    self.whois_info = None
    self.screenshot_file_path = None

    if self.manager is None:
      self.manager = BrowserManager()

  def get_ssl_certificate(self, port = 443):
    context = ssl.create_default_context()
    with socket.create_connection((self.domain, port)) as sock:
      with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
          cert = ssock.getpeercert()
      self.ssl_cert = cert
    self.clock.checkpoint('SSL')

  def get_dns_info(self):
    ips = socket.getaddrinfo(self.domain, None)
    self.dns_info = [ip[4][0] for ip in ips if ip[0] == socket.AF_INET]
    self.clock.checkpoint('DNS')

  def get_mx_records(self):
    mx_records = dns.resolver.resolve(self.domain, 'MX')
    self.mx_info = [str(record.exchange) for record in mx_records]
    self.clock.checkpoint('MX')

  def get_whois_info(self):
    self.whois_info = whois.whois(self.domain)
    self.clock.checkpoint('WHOIS')

  def take_screenshot(self):
    timestring = get_time_string()
    file_path = f'screenshots/{timestring}{self.domain}.png'

    self.manager.push(self.domain, file_path, self)

  def screenshot_callback(self, status, filepath):
    if status:
      self.screenshot_file_path = filepath
    self.clock.checkpoint('SCREENSHOT')
    self.dump()

  def dump(self):

    self.clock.end()

    try:
      entry = {
        'id': self.id,
        'timestamp': time(),
        'main_domain': self.main_domain,
        'domain': self.domain,
        'ssl_cert': self.ssl_cert,
        'dns_info': self.dns_info,
        'mx_info': self.mx_info,
        'whois_info': self.whois_info,
        'screenshot_file_path': self.screenshot_file_path,
        'clock': self.clock.dump()
      }

      logging.info(json.dumps(entry, ensure_ascii=False, default=str))

      filepath = f'{OUTPUT_DIR}/output.ndjson'
      with open(filepath, 'a') as file:
        writer = ndjson.writer(file, ensure_ascii=False, default=str)
        writer.writerow(entry)

      return entry

    except Exception as e:
      print(f'Couldn\'t dump {self.domain}: {str(e)}')

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
    manager = BrowserManager(num_threads)

    with open(input_csv, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for i in range(8): #this loop skips until line N to avoid wasting time
          next(reader)
        for row in reader:
            id, main_domain, correlated_domains_json = row
            correlated_domains = ast.literal_eval(correlated_domains_json)
            for url in set(correlated_domains):
                print(url)
                id = len(urls)
                urls.append((id, main_domain, url))
            g_clock.checkpoint(f'READ_MAIN_DOMAIN_{id}')
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
    args, _ = parser.parse_known_args()
    options['screenshot_only'] = args.screenshot_only

    logging.basicConfig(filename='log.log', level = logging.INFO)

    main(args.input, args.output, args.threads)