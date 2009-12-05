from nose.tools import *
from lamson.testing import *
from lamson.mail import MailRequest, MailResponse
from app.model import archive, mailinglist
import simplejson as json
import shutil

queue_path = archive.store_path('test.list', 'queue')
json_path = archive.store_path('test.list', 'json')

def setup():
    clear_queue(queue_path)
    shutil.rmtree(json_path)

def teardown():
    clear_queue(queue_path)
    shutil.rmtree(json_path)

def test_archive_enqueue():
    msg = MailResponse(From=u'"p\xf6stal Zed" <zedshaw@zedshaw.com>', 
                       To="test.list@librelist.com",
                       Subject="test message", Body="This is a test.")

    archive.enqueue('test.list', msg)
    archived = delivered('zedshaw', to_queue=queue(queue_path))
    assert archived, "Didn't get archived."
    as_string = str(archived)

    assert '-AT-' in str(archived), "Didn't get obfuscated"
    assert '<' in as_string and '"' in as_string and '>' in as_string, "Unicode email screwed up."



def test_white_list_cleanse():
    msg = MailRequest('fakepeer', None, None, open('tests/lots_of_headers.msg').read())
    resp = mailinglist.craft_response(msg, 'test.list', 'test.list@librelist.com')

    archive.white_list_cleanse(resp)
    
    for key in resp.keys():
        assert key in archive.ALLOWED_HEADERS

    assert '@' not in resp['from']
    assert str(resp)

def test_to_json():
    msg = MailRequest('fakeperr', None, None, open("tests/bounce.msg").read())

    resp = mailinglist.craft_response(msg, 'test.list', 'test.list@librelist.com')
    # attach an the message back but fake it as an image it'll be garbage
    resp.attach(filename="tests/bounce.msg", content_type="image/png", disposition="attachment")
    resp.to_message()  # prime the pump

    js = archive.to_json(resp.base)
    assert js

    rtjs = json.loads(js)
    assert rtjs
    assert rtjs['parts'][-1]['encoding']['format'] == 'base64'
