"""
Bounce analysis module for Lamson.  It uses an algorithm that tries
to simply collect the headers that are most likely found in a bounce
message, and then determine a probability based on what it finds.
"""

import re
from functools import wraps


BOUNCE_MATCHERS = {
    'Action': re.compile(r'(failed|delayed|delivered|relayed|expanded)', re.IGNORECASE | re.DOTALL),
    'Content-Description': re.compile(r'(Notification|Undelivered Message|Delivery Report)', re.IGNORECASE | re.DOTALL),
    'Diagnostic-Code': re.compile(r'(.+);\s*([0-9\-\.]+)?\s*(.*)', re.IGNORECASE | re.DOTALL),
    'Final-Recipient': re.compile(r'(.+);\s*(.*)', re.IGNORECASE | re.DOTALL),
    'Received': re.compile(r'(.+)', re.IGNORECASE | re.DOTALL),
    'Remote-Mta': re.compile(r'(.+);\s*(.*)', re.IGNORECASE | re.DOTALL),
    'Reporting-Mta': re.compile(r'(.+);\s*(.*)', re.IGNORECASE | re.DOTALL),
    'Status': re.compile(r'([0-9]+)\.([0-9]+)\.([0-9]+)', re.IGNORECASE | re.DOTALL)
}

BOUNCE_MAX = len(BOUNCE_MATCHERS) * 2.0

PRIMARY_STATUS_CODES = {
    u'1': u'Unknown Status Code 1',
    u'2': u'Success',
    u'3': u'Temporary Failure',
    u'4': u'Persistent Transient Failure',
    u'5': u'Permanent Failure'
}

SECONDARY_STATUS_CODES = {
    u'0':   u'Other or Undefined Status',
    u'1':   u'Addressing Status',
    u'2':   u'Mailbox Status',
    u'3':   u'Mail System Status',
    u'4':   u'Network and Routing Status',
    u'5':   u'Mail Delivery Protocol Status',
    u'6':   u'Message Content or Media Status',
    u'7':   u'Security or Policy Status',
}

COMBINED_STATUS_CODES = {
    u'00': u'Not Applicable',
    u'10': u'Other address status',
    u'11': u'Bad destination mailbox address',
    u'12': u'Bad destination system address',
    u'13': u'Bad destination mailbox address syntax',
    u'14': u'Destination mailbox address ambiguous',
    u'15': u'Destination mailbox address valid',
    u'16': u'Mailbox has moved',
    u'17': u'Bad sender\'s mailbox address syntax',
    u'18': u'Bad sender\'s system address',

    u'20': u'Other or undefined mailbox status',
    u'21': u'Mailbox disabled, not accepting messages',
    u'22': u'Mailbox full',
    u'23': u'Message length exceeds administrative limit.',
    u'24': u'Mailing list expansion problem',

    u'30': u'Other or undefined mail system status',
    u'31': u'Mail system full',
    u'32': u'System not accepting network messages',
    u'33': u'System not capable of selected features',
    u'34': u'Message too big for system',

    u'40': u'Other or undefined network or routing status',
    u'41': u'No answer from host',
    u'42': u'Bad connection',
    u'43': u'Routing server failure',
    u'44': u'Unable to route',
    u'45': u'Network congestion',
    u'46': u'Routing loop detected',
    u'47': u'Delivery time expired',

    u'50': u'Other or undefined protocol status',
    u'51': u'Invalid command',
    u'52': u'Syntax error',
    u'53': u'Too many recipients',
    u'54': u'Invalid command arguments',
    u'55': u'Wrong protocol version',

    u'60': u'Other or undefined media error',
    u'61': u'Media not supported',
    u'62': u'Conversion required and prohibited',
    u'63': u'Conversion required but not supported',
    u'64': u'Conversion with loss performed',
    u'65': u'Conversion failed',

    u'70': u'Other or undefined security status',
    u'71': u'Delivery not authorized, message refused',
    u'72': u'Mailing list expansion prohibited',
    u'73': u'Security conversion required but not possible',
    u'74': u'Security features not supported',
    u'75': u'Cryptographic failure',
    u'76': u'Cryptographic algorithm not supported',
    u'77': u'Message integrity failure',
}

def match_bounce_headers(msg):
    """
    Goes through the headers in a potential bounce message recursively
    and collects all the answers for the usual bounce headers.
    """
    matches = {'Content-Description-Parts': {}}
    for part in msg.base.walk():
        for k in BOUNCE_MATCHERS:
            if k in part.headers:
                if k not in matches:
                    matches[k] = set()

                # kind of an odd place to put this, but it's the easiest way
                if k == 'Content-Description':
                    matches['Content-Description-Parts'][part.headers[k].lower()] = part

                matches[k].add(part.headers[k])

    return matches


def detect(msg):
    """
    Given a message, this will calculate a probability score based on
    possible bounce headers it finds and return a lamson.bounce.BounceAnalyzer
    object for further analysis.

    The detection algorithm is very simple but still accurate.  For each header
    it finds it adds a point to the score.  It then uses the regex in BOUNCE_MATCHERS
    to see if the value of that header is parseable, and if it is it adds another
    point to the score.  The final probability is based on how many headers and matchers
    were found out of the total possible.

    Finally, a header will be included in the score if it doesn't match in value, but
    it WILL NOT be included in the headers used by BounceAnalyzer to give you meanings
    like remote_mta and such.

    Because this algorithm is very dumb, you are free to add to BOUNCE_MATCHERS in your
    boot files if there's special headers you need to detect in your own code.
    """
    originals = match_bounce_headers(msg)
    results = {'Content-Description-Parts':
               originals['Content-Description-Parts']}
    score = 0
    del originals['Content-Description-Parts']

    for key in originals:
        score += 1  # score still goes up, even if value doesn't parse
        r = BOUNCE_MATCHERS[key]

        scan = (r.match(v) for v in originals[key])
        matched = [m.groups() for m in scan if m]

        # a key is counted in the score, but only added if it matches
        if len(matched) > 0:
            score += len(matched) / len(originals[key])
            results[key] = matched

    return BounceAnalyzer(results, score / BOUNCE_MAX)


class BounceAnalyzer(object):
    """
    BounceAnalyzer collects up the score and the headers and gives more
    meaningful interaction with them.  You can keep it simple and just use
    is_hard, is_soft, and probable methods to see if there was a bounce.
    If you need more information then attributes are set for each of the following:

        * primary_status -- The main status number that determines hard vs soft.
        * secondary_status -- Advice status.
        * combined_status -- the 2nd and 3rd number combined gives more detail.
        * remote_mta -- The MTA that you sent mail to and aborted.
        * reporting_mta -- The MTA that was sending the mail and has to report to you.
        * diagnostic_codes -- Human readable codes usually with info from the provider.
        * action -- Usually 'failed', and turns out to be not too useful.
        * content_parts -- All the attachments found as a hash keyed by the type.
        * original -- The original message, if it's found.
        * report -- All report elements, as lamson.encoding.MailBase raw messages.
        * notification -- Usually the detailed reason you bounced.
    """
    def __init__(self, headers, score):
        """
        Initializes all the various attributes you can use to analyze the bounce
        results.
        """
        self.headers = headers
        self.score = score

        if 'Status' in self.headers:
            status = self.headers['Status'][0]
            self.primary_status = int(status[0]), PRIMARY_STATUS_CODES[status[0]]
            self.secondary_status = int(status[1]), SECONDARY_STATUS_CODES[status[1]]
            combined = "".join(status[1:])
            self.combined_status = int(combined), COMBINED_STATUS_CODES[combined]
        else:
            self.primary_status = (None, None)
            self.secondary_status = (None, None)
            self.combined_status = (None, None)

        if 'Remote-Mta' in self.headers:
            self.remote_mta = self.headers['Remote-Mta'][0][1]
        else:
            self.remote_mta = None

        if 'Reporting-Mta' in self.headers:
            self.reporting_mta = self.headers['Reporting-Mta'][0][1]
        else:
            self.reporting_mta = None

        if 'Final-Recipient' in self.headers:
            self.final_recipient = self.headers['Final-Recipient'][0][1]
        else:
            self.final_recipient = None

        if 'Diagnostic-Code' in self.headers:
            self.diagnostic_codes = self.headers['Diagnostic-Code'][0][1:]
        else:
            self.diagnostic_codes = [None, None]
       
        if 'Action' in self.headers:
            self.action = self.headers['Action'][0][0]
        else:
            self.action = None

        # these are forced lowercase because they're so damn random
        self.content_parts = self.headers['Content-Description-Parts']
        # and of course, this isn't the original original, it's the wrapper
        self.original = self.content_parts.get('undelivered message', None)

        if self.original and self.original.parts:
            self.original = self.original.parts[0]

        self.report = self.content_parts.get('delivery report', None)
        if self.report and self.report.parts:
            self.report = self.report.parts

        self.notification = self.content_parts.get('notification', None)


    def is_hard(self):
        """
        Tells you if this was a hard bounce, which is determined by the message
        being a probably bounce with a primary_status greater than 4.
        """
        return self.probable() and self.primary_status[0] > 4

    def is_soft(self):
        """Basically the inverse of is_hard()"""
        return self.probable() and self.primary_status[0] <= 4

    def probable(self, threshold=0.3):
        """
        Determines if this is probably a bounce based on the score 
        probability.  Default threshold is 0.3 which is conservative.
        """
        return self.score > threshold

    def error_for_humans(self):
        """
        Constructs an error from the status codes that you can print to
        a user.
        """
        if self.primary_status[0]:
            return "%s, %s, %s" % (self.primary_status[1],
                                   self.secondary_status[1],
                                   self.combined_status[1])
        else:
            return "No status codes found in bounce message."


class bounce_to(object):
    """
    Used to route bounce messages to a handler for either soft or hard bounces.
    Set the soft/hard parameters to the function that represents the handler.
    The function should take one argument of the message that it needs to handle
    and should have a route that handles everything.

    WARNING: You should only place this on the START of modules that will
    receive bounces, and every bounce handler should return START.  The reason
    is that the bounce emails come from *mail daemons* not the actual person
    who bounced.  You can find out who that person is using
    message.bounce.final_recipient.  But the bounce handler is *actually*
    interacting with a message from something like MAILER-DAEMON@somehost.com.
    If you don't go back to start immediately then you will mess with the state
    for this address, which can be bad.
    """
    def __init__(self, soft=None, hard=None):
        self.soft = soft
        self.hard = hard

        assert self.soft and self.hard, "You must give at least soft and/or hard"

    def __call__(self, func):
        @wraps(func)
        def bounce_wrapper(message, *args, **kw):
            if message.is_bounce():
                if message.bounce.is_soft():
                    return self.soft(message)
                else:
                    return self.hard(message)
            else:
                return func(message, *args, **kw)

        return bounce_wrapper

