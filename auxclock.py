from time import time

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