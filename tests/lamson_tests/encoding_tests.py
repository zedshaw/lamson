from __future__ import with_statement
from nose.tools import *
import re
import os
from lamson import encoding, mail
import mailbox
import email
from email import encoders
from email.utils import parseaddr
from mock import *
import chardet


BAD_HEADERS = [
    u'"\u8003\u53d6\u5206\u4eab" <Ernest.Beard@msa.hinet.net>'.encode('utf-8'),
    '"=?windows-1251?B?RXhxdWlzaXRlIFJlcGxpY2E=?="\n\t<wolfem@barnagreatlakes.com>',
    '=?iso-2022-jp?B?Zmlicm91c19mYXZvcmF0ZUB5YWhvby5jby5qcA==?=<fibrous_favorate@yahoo.co.jp>',

    '=?windows-1252?Q?Global_Leadership_in_HandCare_-_Consumer,\n\t_Professional_and_Industrial_Products_OTC_:_FLKI?=',
    '=?windows-1252?q?Global_Leadership_in_Handcare_-_Consumer, _Auto,\n\t_Professional_&_Industrial_Products_-_OTC_:_FLKI?=',
    'I am just normal.',
    '=?koi8-r?B?WW91ciBtYW6ScyBzdGFtaW5hIHdpbGwgY29tZSBiYWNrIHRvIHlvdSBs?=\n\t=?koi8-r?B?aWtlIGEgYm9vbWVyYW5nLg==?=',
    '=?koi8-r?B?WW91IGNhbiBiZSBvbiB0b3AgaW4gYmVkcm9vbSBhZ2FpbiCWIGp1c3Qg?=\n\t=?koi8-r?B?YXNrIHVzIGZvciBhZHZpY2Uu?=',
    '"=?koi8-r?B?5MXMz9DSz8na18/E09TXzw==?=" <daniel@specelec.com>',
    '=?utf-8?b?IumrlOiCsuWckuWNgOermSDihpIg6ZW35bqa6Yar6Zmi56uZIOKGkiDmlofljJbk?=\n =?utf-8?b?uInot6/nq5kiIDx2Z3hkcmp5Y2lAZG5zLmh0Lm5ldC50dz4=?=',
    '=?iso-8859-1?B?SOlhdnkgTel05WwgVW7uY/hk?=\n\t=?iso-8859-1?Q?=E9?=',
]

DECODED_HEADERS = encoding.header_from_mime_encoding(BAD_HEADERS)

NORMALIZED_HEADERS = [encoding.header_to_mime_encoding(x) for x in DECODED_HEADERS]


def test_MailBase():
    the_subject = u'p\xf6stal'
    m = encoding.MailBase()
    
    m['To'] = "testing@localhost"
    m['Subject'] = the_subject

    assert m['To'] == "testing@localhost"
    assert m['TO'] == m['To']
    assert m['to'] == m['To']

    assert m['Subject'] == the_subject
    assert m['subject'] == m['Subject']
    assert m['sUbjeCt'] == m['Subject']
    
    msg = encoding.to_message(m)
    m2 = encoding.from_message(msg)

    assert_equal(len(m), len(m2))

    for k in m:
        assert m[k] == m2[k], "%s: %r != %r" % (k, m[k], m2[k])
    
    for k in m.keys():
        assert k in m
        del m[k]
        assert not k in m

def test_header_to_mime_encoding():
    for i, header in enumerate(DECODED_HEADERS):
        assert_equal(NORMALIZED_HEADERS[i], encoding.header_to_mime_encoding(header))

def test_dumb_shit():
    # this is a sample of possibly the worst case Mutt can produce
    idiot = '=?iso-8859-1?B?SOlhdnkgTel05WwgVW7uY/hk?=\n\t=?iso-8859-1?Q?=E9?='
    should_be = u'H\xe9avy M\xe9t\xe5l Un\xeec\xf8d\xe9'
    assert_equal(encoding.header_from_mime_encoding(idiot), should_be)

def test_header_from_mime_encoding():
    assert not encoding.header_from_mime_encoding(None)
    assert_equal(len(BAD_HEADERS), len(encoding.header_from_mime_encoding(BAD_HEADERS)))
    
    for i, header in enumerate(BAD_HEADERS):
        assert_equal(DECODED_HEADERS[i], encoding.header_from_mime_encoding(header))


def test_to_message_from_message_with_spam():
    mb = mailbox.mbox("tests/spam")
    fails = 0
    total = 0

    for msg in mb:
        try:
            m = encoding.from_message(msg)
            out = encoding.to_message(m)
            assert repr(out)

            m2 = encoding.from_message(out)

            for k in m:
                if '@' in m[k]:
                    assert_equal(parseaddr(m[k]), parseaddr(m2[k]))
                else:
                    assert m[k].strip() == m2[k].strip(), "%s: %r != %r" % (k, m[k], m2[k])

                assert not m[k].startswith(u"=?")
                assert not m2[k].startswith(u"=?")
                assert m.body == m2.body, "Bodies don't match" 

                assert_equal(len(m.parts), len(m2.parts), "Not the same number of parts.")

                for i, part in enumerate(m.parts):
                    assert part.body == m2.parts[i].body, "Part %d isn't the same: %r \nvs\n. %r" % (i, part.body, m2.parts[i].body)
            total += 1
        except encoding.EncodingError, exc:
            fails += 1

    assert fails/total < 0.01, "There were %d failures out of %d total." % (fails, total)


def test_to_file_from_file():
    mb = mailbox.mbox("tests/spam")
    msg = encoding.from_message(mb[0])

    outfile = "run/encoding_test.msg"

    with open(outfile, 'w') as outfp:
        encoding.to_file(msg, outfp)

    with open(outfile) as outfp:
        msg2 = encoding.from_file(outfp)
    
    outdata = open(outfile).read()

    assert_equal(len(msg), len(msg2))
    os.unlink(outfile)


def test_guess_encoding_and_decode():
    for header in DECODED_HEADERS:
        try:
            encoding.guess_encoding_and_decode('ascii', header.encode('utf-8'))
        except encoding.EncodingError:
            pass


def test_attempt_decoding():
    for header in DECODED_HEADERS:
        encoding.attempt_decoding('ascii', header.encode('utf-8'))


def test_properly_decode_header():
    for i, header in enumerate(BAD_HEADERS):
        parsed = encoding.properly_decode_header(header)
        assert_equal(DECODED_HEADERS[i], parsed)


def test_headers_round_trip():
    # round trip the headers to make sure they convert reliably back and forth
    for header in BAD_HEADERS:
        original = encoding.header_from_mime_encoding(header)

        assert original
        assert "=?" not in original and "?=" not in original, "Didn't decode: %r" % (encoding.SCANNER.scan(header),)

        encoded = encoding.header_to_mime_encoding(original)
        assert encoded

        return_original = encoding.header_from_mime_encoding(encoded)
        assert_equal(original, return_original)

        return_encoded = encoding.header_to_mime_encoding(return_original)
        assert_equal(encoded, return_encoded)


def test_MIMEPart():
    text1 = encoding.MIMEPart("text/plain")
    text1.set_payload("The first payload.")
    text2 = encoding.MIMEPart("text/plain")
    text2.set_payload("The second payload.")

    image_data = open("tests/lamson.png").read()
    img1 = encoding.MIMEPart("image/png")
    img1.set_payload(image_data)
    img1.set_param('attachment','', header='Content-Disposition')
    img1.set_param('filename','lamson.png', header='Content-Disposition')
    encoders.encode_base64(img1)
    
    multi = encoding.MIMEPart("multipart/mixed")
    for x in [text1, text2, img1]:
        multi.attach(x)

    mail = encoding.from_message(multi)

    assert mail.parts[0].body == "The first payload."
    assert mail.parts[1].body == "The second payload."
    assert mail.parts[2].body == image_data

    encoding.to_message(mail)


@patch('chardet.detect', new=Mock())
@raises(encoding.EncodingError)
def test_guess_encoding_fails_completely():
    chardet.detect.return_value = {'encoding': None, 'confidence': 0.0}
    encoding.guess_encoding_and_decode('ascii', 'some data', errors='strict')


def test_attach_text():
    mail = encoding.MailBase()
    mail.attach_text("This is some text.", 'text/plain')

    msg = encoding.to_message(mail)
    assert msg.get_payload(0).get_payload() == "This is some text."
    assert encoding.to_string(mail)

    mail.attach_text("<html><body><p>Hi there.</p></body></html>", "text/html")
    msg = encoding.to_message(mail)
    assert len(msg.get_payload()) == 2
    assert encoding.to_string(mail)


def test_attach_file():
    mail = encoding.MailBase()
    png = open("tests/lamson.png").read()
    mail.attach_file("lamson.png", png, "image/png", "attachment")
    msg = encoding.to_message(mail)

    payload = msg.get_payload(0)
    assert payload.get_payload(decode=True) == png
    assert payload.get_filename() == "lamson.png", payload.get_filename()



def test_content_encoding_headers_are_maintained():
    inmail = encoding.from_file(open("tests/signed.msg"))

    ctype, ctype_params = inmail.content_encoding['Content-Type']

    assert_equal(ctype, 'multipart/signed')

    # these have to be maintained
    for key in ['protocol', 'micalg']:
        assert key in ctype_params

    # these get removed
    for key in encoding.CONTENT_ENCODING_REMOVED_PARAMS:
        assert key not in ctype_params

    outmsg = encoding.to_message(inmail)
    ctype, ctype_params = encoding.parse_parameter_header(outmsg, 'Content-Type')
    for key in ['protocol', 'micalg']:
        assert key in ctype_params, key


def test_odd_content_type_with_charset():
    mail = encoding.MailBase()
    mail.body = u"p\xf6stal".encode('utf-8')
    mail.content_encoding['Content-Type'] = ('application/plain', {'charset': 'utf-8'})

    msg = encoding.to_string(mail)
    assert msg

def test_specially_borked_lua_message():
    assert encoding.from_file(open("tests/borked.msg"))

def raises_TypeError(*args):
    raise TypeError()

@patch('lamson.encoding.MIMEPart.__init__')
@raises(encoding.EncodingError)
def test_to_message_encoding_error(mp_init):
    mp_init.side_effect = raises_TypeError
    test = encoding.from_file(open("tests/borked.msg"))
    msg = encoding.to_message(test)

def raises_UnicodeError(*args):
    raise UnicodeError()

@raises(encoding.EncodingError)
def test_guess_encoding_and_decode_unicode_error():
    data = Mock()
    data.__str__ = Mock()
    data.__str__.return_value = u"\0\0"
    data.decode.side_effect = raises_UnicodeError
    encoding.guess_encoding_and_decode("ascii", data)
    
def test_attempt_decoding_with_bad_encoding_name():
    assert_equal("test", encoding.attempt_decoding("asdfasdf", "test"))

@raises(encoding.EncodingError)
def test_apply_charset_to_header_with_bad_encoding_char():
    encoding.apply_charset_to_header('ascii', 'X', 'bad')

def test_odd_roundtrip_bug():
    decoded_addrs=[u'"\u0414\u0435\u043b\u043e\u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432\u043e" <daniel@specelec.com>',
                   u'"\u8003\u53d6\u5206\u4eab" <Ernest.Beard@msa.hinet.net>',
                   u'"Exquisite Replica"\n\t<wolfem@barnagreatlakes.com>',]

    for decoded in decoded_addrs:
        encoded = encoding.header_to_mime_encoding(decoded)
        assert '<' in encoded and '"' in encoded, "Address wasn't encoded correctly:\n%s" % encoded

