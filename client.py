from tornado import iostream 
import socket
import logging 
logger = logging.getLogger(__name__)
from tornado import gen

class SMTPAsync(object): 
    def __init__(self, host = "localhost", port = 25):
        self.host = host 
        self.port = port 
        self.stream = None

    @gen.coroutine
    def login(self,username, password): 
        if not self.stream: 
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) 
            self.stream = iostream.IOStream(s)
            yield self.stream.connect((self.host, self.port))
            data = yield self.stream.read_until(b'\r\n')
            logger.debug(data)
