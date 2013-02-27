"""
The majority of the server related things Lamson needs to run, like receivers, 
relays, and queue processors.
"""

import smtplib
import smtpd
import asyncore
import threading
import socket
import logging
from lamson import queue, mail, routing
import time
import traceback
from lamson.bounce import PRIMARY_STATUS_CODES, SECONDARY_STATUS_CODES, COMBINED_STATUS_CODES


def undeliverable_message(raw_message, failure_type):
    """
    Used universally in this file to shove totally screwed messages
    into the routing.Router.UNDELIVERABLE_QUEUE (if it's set).
    """
    if routing.Router.UNDELIVERABLE_QUEUE:
        key = routing.Router.UNDELIVERABLE_QUEUE.push(raw_message)

        logging.error("Failed to deliver message because of %r, put it in "
                      "undeliverable queue with key %r", failure_type, key)

class SMTPError(Exception):
    """
    You can raise this error when you want to abort with a SMTP error code to
    the client.  This is really only relevant when you're using the
    SMTPReceiver and the client understands the error.

    If you give a message than it'll use that, but it'll also produce a
    consistent error message based on your code.  It uses the errors in
    lamson.bounce to produce them.
    """
    def __init__(self, code, message=None):
        self.code = code
        self.message = message or self.error_for_code(code)

        Exception.__init__(self, "%d %s" % (self.code, self.message))

    def error_for_code(self, code):
        primary, secondary, tertiary = str(code)
        
        primary = PRIMARY_STATUS_CODES.get(primary, "")
        secondary = SECONDARY_STATUS_CODES.get(secondary, "")
        combined = COMBINED_STATUS_CODES.get(primary + secondary, "")

        return " ".join([primary, secondary, combined]).strip()


class Relay(object):
    """
    Used to talk to your "relay server" or smart host, this is probably the most 
    important class in the handlers next to the lamson.routing.Router.
    It supports a few simple operations for sending mail, replying, and can
    log the protocol it uses to stderr if you set debug=1 on __init__.
    """
    def __init__(self, host='127.0.0.1', port=25, username=None, password=None,
                 ssl=False, starttls=False, debug=0):
        """
        The hostname and port we're connecting to, and the debug level (default to 0).
        Optional username and password for smtp authentication.
        If ssl is True smtplib.SMTP_SSL will be used.
        If starttls is True (and ssl False), smtp connection will be put in TLS mode.
        It does the hard work of delivering messages to the relay host.
        """
        self.hostname = host
        self.port = port
        self.debug = debug
        self.username = username
        self.password = password
        self.ssl = ssl
        self.starttls = starttls

    def configure_relay(self, hostname):
        if self.ssl:
            relay_host = smtplib.SMTP_SSL(hostname, self.port)
        else:
            relay_host = smtplib.SMTP(hostname, self.port)

        relay_host.set_debuglevel(self.debug)

        if self.starttls:
            relay_host.starttls()
        if self.username and self.password:
            relay_host.login(self.username, self.password)

        assert relay_host, 'Code error, tell Zed.'
        return relay_host

    def deliver(self, message, To=None, From=None):
        """
        Takes a fully formed email message and delivers it to the
        configured relay server.

        You can pass in an alternate To and From, which will be used in the
        SMTP send lines rather than what's in the message.
        """
        recipient = To or message['To']
        sender = From or message['From']

        hostname = self.hostname or self.resolve_relay_host(recipient)

        try:
            relay_host = self.configure_relay(hostname)
        except socket.error:
            logging.exception("Failed to connect to host %s:%d" % (hostname, self.port))
            return

        try:
            relay_host.sendmail(sender, recipient, str(message))
        except:
            logging.exception("Failed to send message to host %s:%s" % (hostname, self.port))

        relay_host.quit()

    def resolve_relay_host(self, To):
        import DNS
        address, target_host = To.split('@')
        mx_hosts = DNS.mxlookup(target_host)

        if not mx_hosts:
            logging.debug("Domain %r does not have an MX record, using %r instead.", target_host, target_host)
            return target_host
        else:
            logging.debug("Delivering to MX record %r for target %r", mx_hosts[0], target_host)
            return mx_hosts[0][1]


    def __repr__(self):
        """Used in logging and debugging to indicate where this relay goes."""
        return "<Relay to (%s:%d)>" % (self.hostname, self.port)


    def reply(self, original, From, Subject, Body):
        """Calls self.send but with the from and to of the original message reversed."""
        self.send(original['from'], From=From, Subject=Subject, Body=Body)

    def send(self, To, From, Subject, Body):
        """
        Does what it says, sends an email.  If you need something more complex
        then look at lamson.mail.MailResponse.
        """
        msg = mail.MailResponse(To=To, From=From, Subject=Subject, Body=Body)
        self.deliver(msg)



class SMTPReceiver(smtpd.SMTPServer):
    """Receives emails and hands it to the Router for further processing."""

    def __init__(self, host='127.0.0.1', port=8825):
        """
        Initializes to bind on the given port and host/ipaddress.  Typically
        in deployment you'd give 0.0.0.0 for "all internet devices" but consult
        your operating system.

        This uses smtpd.SMTPServer in the __init__, which means that you have to 
        call this far after you use python-daemonize or else daemonize will
        close the socket.
        """
        self.host = host
        self.port = port
        smtpd.SMTPServer.__init__(self, (self.host, self.port), None)

    def start(self):
        """
        Kicks everything into gear and starts listening on the port.  This
        fires off threads and waits until they are done.
        """
        logging.info("SMTPReceiver started on %s:%d." % (self.host, self.port))
        self.poller = threading.Thread(target=asyncore.loop,
                kwargs={'timeout':0.1, 'use_poll':True})
        self.poller.start()

    def process_message(self, Peer, From, To, Data):
        """
        Called by smtpd.SMTPServer when there's a message received.
        """

        try:
            logging.debug("Message received from Peer: %r, From: %r, to To %r." % (Peer, From, To))
            routing.Router.deliver(mail.MailRequest(Peer, From, To, Data))
        except SMTPError, err:
            # looks like they want to return an error, so send it out
            return str(err)
            undeliverable_message(Data, "Handler raised SMTPError on purpose: %s" % err)
        except:
            logging.exception("Exception while processing message from Peer: %r, From: %r, to To %r." %
                          (Peer, From, To))
            undeliverable_message(Data, "Error in message %r:%r:%r, look in logs." % (Peer, From, To))


    def close(self):
        """Doesn't do anything except log who called this, since nobody should.  Ever."""
        logging.error(traceback.format_exc())


class QueueReceiver(object):
    """
    Rather than listen on a socket this will watch a queue directory and
    process messages it recieves from that.  It works in almost the exact
    same way otherwise.
    """

    def __init__(self, queue_dir, sleep=10, size_limit=0, oversize_dir=None):
        """
        The router should be fully configured and ready to work, the
        queue_dir can be a fully qualified path or relative.
        """
        self.queue = queue.Queue(queue_dir, pop_limit=size_limit,
                                 oversize_dir=oversize_dir)
        self.queue_dir = queue_dir
        self.sleep = sleep

    def start(self, one_shot=False):
        """
        Start simply loops indefinitely sleeping and pulling messages
        off for processing when they are available.

        If you give one_shot=True it will run once rather than do a big
        while loop with a sleep.
        """

        logging.info("Queue receiver started on queue dir %s" %
                     (self.queue_dir))
        logging.debug("Sleeping for %d seconds..." % self.sleep)

        inq = self.queue

        while True:
            keys = inq.keys()

            for key in keys:
                msg = inq.get(key)

                if msg:
                    logging.debug("Pulled message with key: %r off", key)
                    self.process_message(msg)
                    logging.debug("Removed %r key from queue.", key)

	        inq.remove(key)

            if one_shot: 
                return
            else:
                time.sleep(self.sleep)

    def process_message(self, msg):
        """
        Exactly the same as SMTPReceiver.process_message but just designed for the queue's
        quirks.
        """

        try:
            Peer = self.queue_dir # this is probably harmless but I should check it
            From = msg['from']
            To = [msg['to']]

            logging.debug("Message received from Peer: %r, From: %r, to To %r." % (Peer, From, To))
            routing.Router.deliver(msg)
        except SMTPError, err:
            # looks like they want to return an error, so send it out
            logging.exception("Raising SMTPError when running in a QueueReceiver is unsupported.")
            undeliverable_message(msg.original, err.message)
        except:
            logging.exception("Exception while processing message from Peer: "
                              "%r, From: %r, to To %r." % (Peer, From, To))
            undeliverable_message(msg.original, "Router failed to catch exception.")





