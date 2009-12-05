import email
from email.header import make_header, decode_header
from string import capwords
import sys
import mailbox


ALL_MAIL = 0
BAD_MAIL = 0


def all_parts(msg):
    parts = [m for m in msg.walk() if m != msg]
    
    if not parts:
        parts = [msg]

    return parts

def collapse_header(header):
    if header.strip().startswith("=?"):
        decoded = decode_header(header)
        converted = (unicode(
            x[0], encoding=x[1] or 'ascii', errors='replace')
            for x in decoded)
        value = u"".join(converted)
    else:
        value = unicode(header, errors='replace')

    return value.encode("utf-8")


def convert_header_insanity(header):
    if header is None: 
        return header
    elif type(header) == list:
        return [collapse_header(h) for h in header]
    else:
        return collapse_header(header)


def encode_header(name, val, charset='utf-8'):
    msg[name] = make_header([(val, charset)]).encode()


def bless_headers(msg):
    # go through every header and convert it to utf-8
    headers = {}

    for h in msg.keys():
        headers[capwords(h, '-')] = convert_header_insanity(msg[h])

    return headers

def dump_headers(headers):
    for h in headers:
        print h, headers[h]

def mail_load_cleanse(msg_file):
    global ALL_MAIL
    global BAD_MAIL

    msg = email.message_from_file(msg_file)
    headers = bless_headers(msg)

    # go through every body and convert it to utf-8
    parts = all_parts(msg)
    bodies = []
    for part in parts:
        guts = part.get_payload(decode=True)
        if part.get_content_maintype() == "text":
            charset = part.get_charsets()[0]
            try:
                if charset:
                    uguts = unicode(guts, part.get_charsets()[0])
                    guts = uguts.encode("utf-8")
                else:
                    guts = guts.encode("utf-8")
            except UnicodeDecodeError, exc:
                print >> sys.stderr, "CONFLICTED CHARSET:", exc, part.get_charsets()
                BAD_MAIL += 1
            except LookupError, exc:
                print >> sys.stderr, "UNKNOWN CHARSET:", exc, part.get_charsets()
                BAD_MAIL += 1
            except Exception, exc:
                print >> sys.stderr, "WEIRDO ERROR", exc, part.get_charsets()
                BAD_MAIL += 1


            ALL_MAIL += 1

mb = None

try:
    mb = mailbox.Maildir(sys.argv[1])
    len(mb)  # need this to make the maildir try to read the directory and fail
except OSError:
    print "NOT A MAILDIR, TRYING MBOX"
    mb = mailbox.mbox(sys.argv[1])

if not mb:
    print "NOT A MAILDIR OR MBOX, SORRY"

for key in mb.keys():
    mail_load_cleanse(mb.get_file(key))

print >> sys.stderr, "ALL", ALL_MAIL
print >> sys.stderr, "BAD", BAD_MAIL
