from time import time
import multiprocessing
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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
      else:
        return True
      

class WebBrowser:

  manager = None
  NEXT_BROWSER_ID = 0

  def __init__(self, manager = None):
    self.id = self.NEXT_BROWSER_ID
    self.init_browser()
    self.init_task_time = time()
    self.domain = None
    self.domain_instance = None
    WebBrowser.manager = manager
    WebBrowser.NEXT_BROWSER_ID += 1

  def init_browser(self):
    self.free = True

  def take_screenshot(self, url):
    self.domain = url
    self.init_task_time = time()
    if self.free:
      self.free = False
      status = False
      try:
        status = call_timeout(BrowserManager.target_time, self.dotnet_screenshoter)
      except TimeLimitException as e:
        print(f"[BROWSER] Timed out!")
      except Exception as e:
        print(f"[BROWSER {self.id}] - Error: {str(e)}")
      
      if status and isinstance(self.manager, BrowserManager):
        self.free = True
        self.manager.free_callback(self)
      else:
        self.interrupt()

      return status
    else:
      raise Exception(f'[BROWSER {self.id}] {url}: take_screenshot called when busy')

  def dotnet_screenshoter(self):
    print(f"[BROWSER {self.id}] START screenshot phase for {self.domain}")
    try:
      result = subprocess.run(f"/app/screenshoter/PhishingCrawler {self.domain}",
                              shell=True, 
                              check=True, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True
                            )
      print(f"[BROWSER {self.id}] Successfully taken screenshot for {self.domain}")
    except subprocess.CalledProcessError as e:
      print(f"Couldn't take screenshot for {self.domain}... {str(e)}")
      self.interrupt()

    print(f"[BROWSER {self.id}] End screenshot phase for {self.domain}")

  def interrupt(self):
    print(f'[BROWSER {self.id}] INTERRUPTING AND RESTARTING')
    self.manager = BrowserManager()
    self.init_browser()
    self.init_task_time = time()
    self.manager.free_callback(self)
    
    
class BrowserManager:

  queue = []
  num_instances = 1
  instances = []
  target_time = 10
  free_instances = set()

  def __init__(self, num_instances = -1, target_time = 10):
    if num_instances == -1:
      num_instances = BrowserManager.num_instances
    BrowserManager.target_time = target_time
    BrowserManager.num_instances = num_instances
    while len(BrowserManager.instances) < num_instances:
        print(f'[BROWSERMANAGER] CREATING NEW INSTANCE. NUM_INSTANCES = {len(BrowserManager.instances) + 1}/{BrowserManager.num_instances}')
        browser = WebBrowser(self)
        BrowserManager.instances.append(browser)
        BrowserManager.free_instances.add(browser)

  # Check if there is a free web browser and a site to process
  @classmethod
  def checkQueue(cls):
    if len(cls.free_instances) > 0 and len(cls.queue) > 0:
      browser = cls.free_instances.pop()
      domain = cls.pop_domain()
      if domain is not None:
        (url, file_path, instance) = domain
        instance.clock.checkpoint('SCREENSHOT_DEQUEUED')
        print(f'[MANAGER] BROWSER {browser.id} is now BUSY')
        status = browser.take_screenshot(url)
        instance.screenshot_callback(status, file_path)
    cls.checkForCrashes()


  @classmethod
  def checkForCrashes(cls):
    for i, browser in enumerate(cls.instances):
      time_executing = time() - browser.init_task_time
      if not browser.free and time_executing >= cls.target_time:
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