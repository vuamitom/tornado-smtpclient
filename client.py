"""
Port the standard smtplib for use with tornado non-blocking application model 
"""

from tornado import iostream 
import socket
import logging 
logger = logging.getLogger(__name__)
from tornado import gen

try: 
    import ssl 
except: 
    _have_ssl = False
else:
    class SSLFakeFile(object):
        def __init__(self, sslobj):
            self.sslobj = sslobj 
        def readLine(self): 
            str = ""
            chr = None 
            while chr != "\n":
                chr = self.sslobj.read(1)
                if not chr: break 
                str += chr 
            return str 
             
    _have_ssl = True

errors = {
    501 : 'Syntax error in parameters or arguments'
}
CRCF = b'\r\n'

class SMTPAsync(object): 
    def __init__(self, host = None, port = None):
        self.host = host 
        self.port = port 
        self.stream = None
        self.sock = None
        self.esmtp_features = {} 
        self.file = None
        self.done_esmtp = 0
        self.helo_resp = None 
        self.ehlo_resp = None

    def has_extn(self, f): 
        return True 
            
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
        request = b''.join([name,b' ', param, CRCF]) if param else b''.join([name, CRCF])  
        self.stream.write(request)  
        response = yield self.stream.read_until(CRCF)

        # some commands such as ehlo returns a list of <code>-<subCommand>\r\n<code>-<subCommand> 
        # before the final status code. Ignore them for now
        while response[3] not in b' \r\n':
            response = yield self.stream.read_until(CRCF)

        code = int(response[0:3])
        if not 200 <= code < 300: 
            raise CommandError("Response code %s: %s" % (code, errors.get(code, response[3:])))
        return (code, response[3:])


    @gen.coroutine
    def connect(self, host = None, port = None):
        self.host = host if host else self.host 
        self.prot = port if port else self.port 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) 
        self.stream = iostream.IOStream(self.sock)
        # seem like I don't need to put 'yield' here 
        # strange, I thought it should wait until connection established          
        # and then read data from stream. Maybe the stream api is forcing a wait on read_until call 
        self.stream.connect((self.host, self.port)) 
        response = yield self.stream.read_until(CRCF)
        code = int(response[0:3])
        if not 200 <= code < 300: 
            raise ConnectionError(response[3:])
        return (code, response[3:]) 

    @gen.coroutine
    def starttls(self, keyfile=None, certfile=None): 
        #TODO: check how to read the local computer name
        yield self.ehlo_or_helo_if_needed() 
        if not self.has_extn('starttls'): 
            raise SMTPError('STARTTLS extension not supported ') 

        code, msg = yield self._command(b'STARTTLS')
        if code == 220: 
            if not _have_ssl: 
                raise RuntimeError("No SSL support included in this Python ")
            self.sock = ssl.wrap_socket(self.sock, keyfile, certfile, do_handshake_on_connect= False) 
            self.sock.do_handshake()
            self.file = SSLFakeFile(self.sock)
            self.helo_resp = None 
            self.ehlo_resp = None 
            self.esmtp_features = {}
            self.does_esmtp = 0 
        return (code, msg)
       
    @gen.coroutine
    def ehlo_or_helo_if_needed(self): 
        if not self.helo_resp and not self.ehlo_resp: 
            code, resp = yield self.ehlo()   
            if not (200<= code <300):
                code, resp = yield self.helo()
                if not (200 <= code < 300): 
                    raise ConnectionError("Hello error")


    @gen.coroutine
    def helo(self):
        raise NotImplementedError()

    @gen.coroutine
    def ehlo(self):        
        code, resp = yield self._command(b'ehlo', b'localhost') 
        self.ehlo_resp = resp 
        if code == -1 and len (resp) == 0 : 
            self.close()
            raise ConnectionError("Server not connected")
        return (code, resp)



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
class SMTPError(Exception):
    pass 
