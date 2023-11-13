import socket

class CaptureSocket:
    
    host = "127.0.0.1"
    port = 9018
    
    def get_screenshot(self, url):
        """
            Returns path to file
        """
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(20)
        s.connect((self.host, self.port))

        try:
            s.send(bytearray(url, 'utf-8'))
            s.close()
            return False, None            
        except Exception as e:
            print("[CAPTURE SOCKET] " + str(e))
            return False, None 
 
    def terminate(self):
        """
            Sends termination signal
        """
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(20)
        s.connect((self.host, self.port))

        try:
            s.send(bytearray("finished", 'utf-8'))
            result = s.recv(1024).decode()
            s.close()
            return result is not None and result == "Finished"
        except Exception as e:
            print("[CAPTURE SOCKET] " + str(e))
            return False