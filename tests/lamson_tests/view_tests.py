from nose.tools import *
from lamson import view
import jinja2


def test_load():
    template = view.load("template.txt")
    assert template
    assert template.render()

def test_render():
    # try with some empty vars
    text = view.render({}, "template.txt")
    assert text


def test_most_basic_form():
    msg = view.respond(locals(), 'template.txt')
    assert msg.Body

def test_respond_cadillac_version():
    dude = 'Tester'

    msg = view.respond(locals(), Body='template.txt', 
                      Html='template.html',
                      From='test@localhost',
                      To='receiver@localhost',
                      Subject='Test body from "%(dude)s".')

    assert msg.Body
    assert msg.Html

    for k in ['From', 'To', 'Subject']:
        assert k in msg


def test_respond_plain_text():
    dude = 'Tester'

    msg = view.respond(locals(), Body='template.txt', 
                      From='test@localhost',
                      To='receiver@localhost',
                      Subject='Test body from "%(dude)s".')

    assert msg.Body
    assert not msg.Html

    for k in ['From', 'To', 'Subject']:
        assert k in msg



def test_respond_html_only():
    dude = 'Tester'

    msg = view.respond(locals(), Html='template.html', 
                      From='test@localhost',
                      To='receiver@localhost',
                      Subject='Test body from "%(dude)s".')

    assert not msg.Body
    assert msg.Html

    for k in ['From', 'To', 'Subject']:
        assert k in msg



def test_respond_attach():
    dude = "hello"
    mail = view.respond(locals(), Body="template.txt",
                       From="test@localhost",
                       To="receiver@localhost",
                       Subject='Test body from someone.')

    view.attach(mail, locals(), 'template.html', content_type="text/html",
               filename="template.html", disposition='attachment')

    assert_equal(len(mail.attachments), 1)

    msg = mail.to_message()
    assert_equal(len(msg.get_payload()), 2)
    assert str(msg)

    mail.clear()

    view.attach(mail, locals(), 'template.html', content_type="text/html")
    assert_equal(len(mail.attachments), 1)

    msg = mail.to_message()
    assert_equal(len(msg.get_payload()), 2)
    assert str(msg)


def test_unicode():
    dude = u'H\xe9avy M\xe9t\xe5l Un\xeec\xf8d\xe9'
    mail = view.respond(locals(), Html="unicode.html",
                       From="test@localhost",
                       To="receiver@localhost",
                       Subject='Test body from someone.')
    assert str(mail)

    view.attach(mail, locals(), "unicode.html", filename="attached.html")

    assert str(mail)

