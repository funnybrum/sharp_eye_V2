from functools import wraps
from time import time
from . import config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def result_interceptor(interceptor):
    def ri_wrapper(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = None
            exc = None
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                exc = e
                raise
            finally:
                interceptor(result=result, exception=exc)
        return wrapper
    return ri_wrapper


def stats_wrapper(name, stats_callback):
    def s_wrapper(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time()
            try:
                return f(*args, **kwargs)
            finally:
                stats_callback(name, time() - start)
        return wrapper
    return s_wrapper


def send_email(subject, message, attachments={}):
    smtp_config = config['smtp']

    # Prepare actual message
    body = MIMEMultipart()
    body['From'] = smtp_config['sender']
    body['To'] = smtp_config['recipient']
    body['Subject'] = subject

    body.attach(MIMEText(message))
    for attachment in attachments:
        body.attach(MIMEApplication(
            attachment['data'].read(),
            Content_Disposition='attachment; filename="%s"' % attachment['name'],
            Name=attachment['name']
        ))

    server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
    server.ehlo()
    server.starttls()
    server.login(smtp_config['user'], smtp_config['password'])
    server.sendmail(smtp_config['user'], smtp_config['recipient'], body.as_string())
    server.close()
