from time import time
import ssl
import socket
from time import time
import tldextract
import whois
import dns.resolver
import json
import ndjson
import logging
from datetime import datetime
from auxclock import AuxClock
from browsermanager import BrowserManager

OUTPUT_DIR = 'output'

def get_time_string():
    now = datetime.now()
    return now.strftime('%Y-%m-%d-%H-%M-%S')

class Domain:
  manager = None

  def __init__(self, id, main_domain, url, DNS=None):
    self.NS = ['8.8.8.8', '4.4.4.4'] 
    self.id = id
    self.clock = AuxClock()
    self.main_domain = main_domain
    ext = tldextract.extract(url)
    self.domain = f'{ext.domain}.{ext.suffix}'
    self.ssl_cert = None
    self.dns_info = None
    self.dns_cname = None
    self.mx_info = None
    self.whois_info = None
    self.screenshot_file_path = None

    # set DNS name server
    if DNS: 
      self.NS = [DNS]
    dns.resolver.nameservers = self.NS

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
    ips = dns.resolver.resolve(self.domain, 'A')
    self.dns_info = [str(record.exchange) for record in ips]    
    ips = dns.resolver.resolve(self.domain, 'CNAME')
    self.dns_cname = [str(record.exchange) for record in ips]
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
        'dns_cname': self.dns_cname,
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
