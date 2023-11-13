import socket

class CaptureSocket:
    
    host = "127.0.0.1"
    port = 9018
    
    def __init__(self):
        self.s = None
        self.start()
    
    def start(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setblocking(0)
            self.s.connect((self.host, self.port))
        except Exception as e:
            print(e)

    def get_screenshot(self, url):
        """
            Returns path to file
        """
        
        self.start()

        try:
            self.s.send(bytearray(url, 'utf-8'))
            self.s.close()
            return False, None            
        except Exception:
            return False, None 
 
    def terminate(self):
        """
            Sends termination signal
        """
        self.start()
        try:
            self.s.send(bytearray("finished", 'utf-8'))
            result = self.s.recv(1024).decode()
            self.s.close()
            return result is not None and result == "Finished"
        except Exception:
            return False