from nose.tools import *
from app.model import html



def test_strip_html():
    doc = """<html><body>
        <h1>Title 1</h1>
        <p>Hello there.</p>
        <p>I like your shirt.</p>
        <p><a href="http://myinboxisnota.tv">Go here for help.</a></p>
        </body></html>
        """
    txt = html.strip_html(doc)

    assert txt
    assert_not_equal(txt, html)
    assert "<" not in txt


def test_strip_big_html():
    doc = open("tests/index.html").read()
    txt = html.strip_html(doc)
    assert txt
    assert_not_equal(txt, html)
    assert "<" not in txt

