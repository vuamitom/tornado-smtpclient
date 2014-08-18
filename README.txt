Non-blocking smtp client to work with tornado web framework 4.0 and above

This library is a port of Python smtplib to tornado non-blocking IOstream implementation.

The below example was taken and modified from Python docs' example::

    #!/usr/bin/env python3

    from tornado_smtpclient import client 

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # create SMTP client
    s = client.SMTPAsync()
    yield s.connect('your.email.host',587)
    yield s.starttls()
    yield s.login('username', 'password')

    # me == my email address
    # you == recipient's email address
    me = "my@email.com"
    you = "your@email.com"

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

    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    yield s.sendmail(me, you, msg.as_string())
    yield s.quit()

