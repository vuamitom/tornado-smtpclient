from tornado import iostream 
import socket
import logging 
logger = logging.getLogger(__name__)
from tornado import gen


errors = {
    501 : 'Syntax error in parameters or arguments'
}

class SMTPAsync(object): 
    def __init__(self, host = None, port = None):
        self.host = host 
        self.port = port 
        self.stream = None
        self.state = None # keep the last command 
    
    @gen.coroutine
    def _command(self, name, param = None): 
        if not self.stream: 
            raise StreamError("IOStream is not yet created")
        if self.stream.closed():
            raise StreamError("Stream is already closed")
        if self.stream.writing(): 
            # we can handle this case better than just throwing out 
            # an error 
            raise StreamError("Stream is occupied at the moment")

        # check if we really need to yield here      
        request = b''.join([name,b' ', param, b'\r\n']) if param else b''.join([name, b'\r\n'])  
        self.stream.write(request)  
        response = yield self.stream.read_until(b'\r\n')

        # some commands such as ehlo returns a list of <code>-<subCommand>\r\n<code>-<subCommand> 
        # before the final status code. Ignore them for now
        while response[3] not in b' \r\n':
            response = yield self.stream.read_until(b'\r\n')

        code = int(response[0:3])
        if not 200 <= code < 300: 
            raise CommandError("Response code %s: %s" % (code, errors.get(code, response[3:])))
        return (code, response[3:])


    @gen.coroutine
    def connect(self, host = None, port = None):
        self.host = host if host else self.host 
        self.prot = port if port else self.port 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) 
        self.stream = iostream.IOStream(s)
        # seem like I don't need to put 'yield' here 
        # strange, I thought it should wait until connection established          
        # and then read data from stream. Maybe the stream api is forcing a wait on read_until call 
        self.stream.connect((self.host, self.port)) 
        response = yield self.stream.read_until(b'\r\n')
        code = int(response[0:3])
        if not 200 <= code < 300: 
            raise ConnectionError(response[3:])
        return (code, response[3:]) 

    @gen.coroutine
    def starttls(self): 
        #TODO: check how to read the local computer name
        yield self._command(b'ehlo', b'localhost') 
        res = yield self._command(b'STARTTLS')
        return res 
       

    @gen.coroutine
    def login(self,username, password): 
            yield self.stream.connect((self.host, self.port))
            data = yield self.stream.read_until(b'\r\n')
            logger.debug(data)

    def quit():
        pass 

class StreamError(Exception): 
    pass  
class CommandError(Exception): 
    pass
class ConnectionError(Exception):
    pass 
