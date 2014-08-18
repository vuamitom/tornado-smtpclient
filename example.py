from tornado.options import options, parse_command_line

options.log_to_stderr=True
options.logging="debug"
import logging
logger = logging.getLogger(__name__)

from tornado.smtp.client import SMTPAsync
import tornado.ioloop
from tornado import gen

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

@gen.coroutine
def send_email():
    logger.debug("--SMTP Client--") 
    try:
        s = SMTPAsync()
        response = yield s.connect('email-smtp.us-east-1.amazonaws.com',587)
        logger.debug(response)
        logger.debug("done connect")
        yield s.starttls()
        (code, resp) = yield s.login('AKIAJDTRW7NC2S4O5YNQ','AlNCBc5EQ258Gv3nl5kabfA9EoSdGEll3yAVTSOLF8+E')
        logger.debug(code)
        logger.debug(resp)

        #senderrs = yield s.sendmail("lienhe@kiotviet.com", "tamvu89@gmail.com", "HELLO THERE")
        #logger.debug(senderrs)


        me = "lienhe@kiotviet.com"
        you = "tamvu89@gmail.com"

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Link"
        msg['From'] = me
        msg['To'] = you

        # Create the body of the message (a plain-text and an HTML version).
        text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
        html = """\
        <html>
          <head></head>
          <body>
            <p>Hi!<br>
               How are you?<br>
               Here is the <a href="http://www.python.org">link</a> you wanted.
            </p>
          </body>
        </html>
        """

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        yield s.sendmail(me, you, msg.as_string())
        yield s.quit()
    except Exception as e:
        logger.exception(e)
    finally: 
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":  
    parse_command_line()
    loop = tornado.ioloop.IOLoop.instance()
    loop.add_callback(callback=send_email)
    loop.start()
   
