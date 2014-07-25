"""
Port the standard smtplib for use with tornado non-blocking application model 
"""

from tornado import iostream 
import socket
import logging 
logger = logging.getLogger(__name__)
from tornado import gen
import smtplib
import re
import base64
import hmac
from base64 import b64encode as encode_base64

try: 
    import ssl 
except ImportError:
    _have_ssl = False
else:
    _have_ssl = True

errors = {
    501 : 'Syntax error in parameters or arguments'
}
CRCF = b'\r\n'

class SMTPAsync(object):
    file = None
    helo_resp = None
    ehlo_msg = b'ehlo'
    ehlo_resp = None
    does_esmtp = 0

    def __init__(self, host = '', port = 0, local_hostname = None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.default_port = smtplib.SMTP_PORT
        self.stream = None
        self.timeout = timeout
        self.sock = None
        self.esmtp_features = {}


        if local_hostname: 
            self.local_hostname = local_hostname 
        else:
            fqdn = socket.getfqdn() 
            if '.' in fqdn:
                self.local_hostname = bytes(fqdn, 'utf-8') 
            else: 
                addr = '127.0.0.1' 
                try: 
                    addr = socket.gethostbyname(socket.gethostname())
                except socket.gaierror: 
                    pass 
                self.local_hostname = '[%s]' % addr

    def _get_stream(self, host, port, timeout):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = iostream.IOStream(self.sock)
        self.stream.connect((host, port))
        return self.stream


    def has_extn(self, opt):
        return opt.lower() in self.esmtp_features

    @gen.coroutine
    def doccmd(self, cmd, args = None):
        self.putcmd(cmd, args)
        (code, msg) = yield self.getreply()
        return (code, msg)

    @gen.coroutine
    def putcmd(self, name, param = None):
        if not self.stream: 
            raise SMTPAsyncException("IOStream is not yet created")
        if self.stream.closed():

            raise SMTPAsyncException("Stream is already closed")
        if self.stream.writing(): 
            # we can handle this case better than just throwing out 
            # an error 
            raise SMTPAsyncException("Stream is occupied at the moment")

        # check if we really need to yield here      
        request = b''.join([name,b' ', param, CRCF]) if param else b''.join([name, CRCF])  
        yield self.stream.write(request)



    @gen.coroutine
    def getreply(self):

        resp = []
        while True:
            try:
                response = yield self.stream.read_until(CRCF)
                logger.debug(response)
            except socket.error:
                raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")
            resp.append(response[4:])
            code = response[0:3]
            try:
                code= int(code)
            except ValueError:
                code = -1
                break

            if response[3] in b' \r\n':
                break
        msg = b'\n'.join(resp)
        return (code,msg)

    @gen.coroutine
    def connect(self, host = None, port = None):
        if not port and (host.find(':') == host.rfind(':')):
            i = host.rfind(':')
            if i >= 0:
                host, port = host[:i], host[i+1:]
                try:
                    port = int(port)
                except ValueError:
                    raise socket.error("nonnumeric port")

        if not port: port = self.default_port
        self.stream =  self._get_stream(host, port, self.timeout)
        (code, msg) = yield self.getreply()
        return (code, msg)


    @gen.coroutine
    def starttls(self, keyfile=None, certfile=None): 
        #TODO: check how to read the local computer name
        yield self.ehlo_or_helo_if_needed() 
        if not self.has_extn('starttls'): 
            raise smtplib.SMTPException('STARTTLS extension not supported ')

        code, msg = yield self.doccmd(b'STARTTLS')
        if code == 220: 
            if not _have_ssl: 
                raise RuntimeError("No SSL support included in this Python ")
            self.sock = ssl.wrap_socket(self.sock, keyfile, certfile, do_handshake_on_connect= False) 
            # set blocking = True. Otherwise, exception will be thrown. I don't know how to make it non-blocking here yet
            # self.stream = IOStream(self.sock)
            self.sock.do_handshake(True)
            self.file = SSLFakeFile(self.sock)
            self.helo_resp = None 
            self.ehlo_resp = None 
            self.esmtp_features = {}
            self.does_esmtp = 0 
        return (code, msg)

    @gen.coroutine
    def login(self, username, password):
        def encode_cram_md5(challenge, username, password): 
            challenge = base64.decodestring(challenge)
            response = username + " " + hmac.MAC(password, challenge).hexdigest() 
            return encode_base64(response, eol="")

        def encode_plain(user, password): 
            return encode_base64("\0%s\0%s" % (user, password), eol="")

        AUTH_PLAIN = "PLAIN"
        AUTH_CRAM_MD5 = "CRAM-MD5"
        AUTH_LOGIN = "LOGIN"

        yield self.ehlo_or_helo_if_needed()
        if not self.has_extn('auth'):
            raise smtplib.SMTPException("SMTP Auth extension not supported by server ")
        authlist = self.esmtp_features['auth'].split()
        preferred_auths = [AUTH_CRAM_MD5, AUTH_PLAIN, AUTH_LOGIN]
        
        authmethod = None
        for method in preferred_auths:
            if method in authlist:
                authmethod = method
                break

        if authmethod == AUTH_CRAM_MD5: 
            code, msg = yield self.doccmd("AUTH", AUTH_CRAM_MD5)
            if code == 503:
                #alr authenticated
                return (code, msg) 
            code, msg = yield self.doccmd(encode_cram_md5(msg, username, password))
        elif authmethod == AUTH_PLAIN: 
            code, msg = yield self.doccmd("AUTH", AUTH_PLAIN + " " + encode_plain(username, password))
        elif authmethod == AUTH_LOGIN: 
            code, msg = yield self.doccmd("AUTH","%s %s" % (AUTH_LOGIN, encode_base64(username, eol="")))
            if code != 334: 
                raise smtplib.SMTPAuthenticationError(code,msg)
            code, msg = yield self.doccmd(encode_base64(password, eol=""))

        elif authmethod is None: 
            raise smtplib.SMTPException("No suitable authentication method found.")
        if code not in (235, 503): 
            raise smtplib.SMTPAuthenticationError(code, msg)

        return (code,msg) 
       
    @gen.coroutine
    def ehlo_or_helo_if_needed(self): 
        if not self.helo_resp and not self.ehlo_resp: 
            code, resp = yield self.ehlo()   
            if not (200<= code <300):
                code, resp = yield self.helo()
                if not (200 <= code < 300): 
                    raise ConnectionError("Hello error")


    @gen.coroutine
    def helo(self, name = None):

        self.putcmd("helo", name or self.local_hostname)
        (code,msg)= yield self.getreply()
        self.helo_resp=msg
        return (code,msg)



    @gen.coroutine
    def ehlo(self, name=''):
        self.esmtp_features = {}
        self.putcmd(self.ehlo_msg,  name or self.local_hostname)
        (code, msg) = yield self.getreply()

        self.ehlo_resp = msg
        if code == -1 and len (msg) == 0 :
            self.close()
            raise smtplib.SMTPServerDisconnected("Server not connected")

        if code != 250:
            return (code, msg)
        self.does_esmtp =1

        #parse the ehlo response -ddm
        resp=self.ehlo_resp.split(b'\n')
        del resp[0]
        for each in resp:

            auth_match = smtplib.OLDSTYLE_AUTH.match(each)
            if auth_match:
                # This doesn't remove duplicates, but that's no problem
                self.esmtp_features["auth"] = self.esmtp_features.get("auth", "") \
                        + " " + auth_match.groups(0)[0]
                continue

            # RFC 1869 requires a space between ehlo keyword and parameters.
            # It's actually stricter, in that only spaces are allowed between
            # parameters, but were not going to check for that here.  Note
            # that the space isn't present if there are no parameters.
            m= re.match(r'(?P<feature>[A-Za-z0-9][A-Za-z0-9\-]*) ?',each)
            if m:
                feature=m.group("feature").lower()
                params=m.string[m.end("feature"):].strip()
                if feature == "auth":
                    self.esmtp_features[feature] = self.esmtp_features.get(feature, "") \
                            + " " + params
                else:
                    self.esmtp_features[feature]=params
        return (code,msg)

    @gen.coroutine
    def login(self,username, password): 
            yield self.stream.connect((self.host, self.port))
            data = yield self.stream.read_until(b'\r\n')
            logger.debug(data)

    def quit(self):
        pass 

class SMTPAsyncException(Exception):
    pass
