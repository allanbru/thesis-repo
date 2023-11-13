from time import time
import ssl
import socket
import tldextract
import whois
import dns.resolver
import json
import ndjson
import logging
from datetime import datetime
from auxclock import AuxClock
from capture_socket import CaptureSocket

OUTPUT_DIR = 'output'

def get_time_string():
    now = datetime.now()
    return now.strftime('%Y-%m-%d-%H-%M-%S')

class Domain:

  NS = ["8.8.8.8", "4.4.4.4"]

  def __init__(self, id, main_domain, url, DNS = None):
    self.id = id
    self.clock = AuxClock()
    self.main_domain = main_domain
    ext = tldextract.extract(url)
    self.domain = f'{ext.domain}.{ext.suffix}'
    self.ssl_cert = None
    self.a_info = None
    self.aaaa_info = None
    self.cname_info = None
    self.mx_info = None
    self.whois_info = None
    self.screenshot_file_path = None
    self.server = CaptureSocket()
    print(f"Started {self.domain}")

    if DNS is not None:
      NS = DNS
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = NS

  def get_ssl_certificate(self, port = 443):
    context = ssl.create_default_context()
    try:
      with socket.create_connection((self.domain, port)) as sock:
        with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
            cert = ssock.getpeercert()
        self.ssl_cert = cert
    except:
      pass
    self.clock.checkpoint('SSL')

  def get_dns_info(self):
    try:
      ips = dns.resolver.resolve(self.domain, "A")
      self.a_info = [str(ip) for ip in ips]
    except:
      pass
    self.clock.checkpoint('DNS A')
    self.get_aaaa_info()

  def get_aaaa_info(self):
    try:
      ips = dns.resolver.resolve(self.domain, "AAAA")
      self.aaaa_info = [str(ip) for ip in ips]
    except:
      pass
    self.clock.checkpoint('DNS AAAA')
    self.get_cname_info()

  def get_cname_info(self):
    try:
      ips = dns.resolver.resolve(self.domain, "CNAME")
      self.cname_info = [str(ip) for ip in ips]
    except:
      pass
    self.clock.checkpoint('DNS CNAME')

  def get_mx_records(self):
    try:
      mx_records = dns.resolver.resolve(self.domain, 'MX')
      self.mx_info = [str(record.exchange) for record in mx_records]
    except:
      pass
    self.clock.checkpoint('MX')

  def get_whois_info(self):
    try:
      self.whois_info = whois.whois(self.domain)
      self.clock.checkpoint('WHOIS')
    except:
      pass

  def take_screenshot(self):
    if self.a_info is not None or self.aaaa_info is not None or self.cname_info is not None:
      self.__screenshot__()

  def __screenshot__(self):
    self.clock.checkpoint('SCREENSHOT_START')
    self.server.get_screenshot(self.domain)
    self.screenshot_callback(False, None)

  def screenshot_callback(self, status, filepath):
    if status:
      self.clock.checkpoint('SCREENSHOT')
      self.screenshot_file_path = filepath
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
        'a_info': self.a_info,
        'aaaa_info': self.aaaa_info,
        'cname_info': self.cname_info,
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