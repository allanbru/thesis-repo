import socket

class CaptureSocket:
    
    host = "127.0.0.1"
    port = 9018

    @classmethod
    def get_screenshot(cls, url):
        """
            Returns path to file
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #s.setblocking(0)
            s.settimeout(30.0)
            s.connect((cls.host, cls.port))
            s.send(bytearray(url, 'utf-8'))
            #result = s.recv(1024).decode()
            s.close()
            #if result.startswith("Success:"):
            #    return True, result.removeprefix("Success: ")
            return False, None            
        except Exception:
            return False, None 