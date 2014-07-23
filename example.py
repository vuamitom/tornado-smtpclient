from tornado.options import options, parse_command_line
options.log_to_stderr=True
options.logging="debug"
import logging
logger = logging.getLogger(__name__)

import client
import tornado.ioloop
from tornado import gen

@gen.coroutine
def send_email():
    logger.debug("--SMTP Client--") 
    try:
        s = client.SMTPAsync('email-smtp.us-east-1.amazonaws.com', 587)
        response = yield s.connect()
        logger.debug(response)
        logger.debug("done connect")
        yield s.starttls()
    except Exception as e: 
        logger.exception(e)
    finally: 
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":  
    parse_command_line()
    loop = tornado.ioloop.IOLoop.instance()
    loop.add_callback(callback=send_email)
    loop.start()
   
