from tornado import iostream 
import socket
import logging 
logger = logging.getLogger(__name__)
from tornado import gen

class SMTPAsync(object): 
    def __init__(self, host = None, port = None):
        self.host = host 
        self.port = port 
        self.stream = None
        self.state = None # keep the last command 
    
    def _command(name, param): 
        if not self.stream: 
            raise NoneStreamError("IOStream is not yet created")
        if self.stream.closed():
            raise ClosedStreamError("Stream is already closed")

        # check if we really need to yield here      
        yield self.stream.write(''.join(name, param, "\r\n")  
        response = yield self.stream.read_until(b'\r\n')
        return (int(response[0:3]), response[3:])


    @gen.coroutine
    def connect(self, host = None, port = None):
        self.host = host if host else self.host 
        self.prot = port if port else self.port 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) 
        self.stream = iostream.IOStream(s)
        yield self.stream.connect((self.host, self.port)) 

    @gen.coroutine
    def starttls(): 
        pass 

    @gen.coroutine
    def login(self,username, password): 
            yield self.stream.connect((self.host, self.port))
            data = yield self.stream.read_until(b'\r\n')
            logger.debug(data)

    def quit():
        pass 

class NoneStreamError(Exception): 
    pass  

class ClosedStreamError(Exception):
    pass 
