from nose.tools import *
from config import testing
from lamson import html, view, mail



def test_HtmlMail_load_css():
    title = "load_css Test"
    hs = html.HtmlMail("style.css", "html_test.html")
    assert_equal(len(hs.stylesheet), 8)
    assert_equal(hs.stylesheet[0][0], u"body")


def test_HtmlMail_apply_styles():
    hs = html.HtmlMail("style.css", "html_test.html")
    page = view.render(locals(), "html_test.html")

    styled = hs.apply_styles(page)

    assert "magenta" in str(styled)
    assert_not_equal(str(styled), str(page))


def test_HtmlMail_render():
    title = "render Test"
    hs = html.HtmlMail("style.css", "html_test.html")

    lame = hs.render(locals(), "content.markdown")
    assert lame

    pretty = hs.render(locals(), "content.markdown", pretty=True)

    assert pretty
    assert_not_equal(lame, pretty)


def test_HtmlMail_respond():
    title = "respond Test"
    hs = html.HtmlMail("style.css", "html_test.html")
    variables = locals()

    msg = hs.respond(variables, "content.markdown", From='somedude@localhost',
                     To='zed.shaw@gmail.com',
                     Subject='This is a %(title)s')

    assert 'content' not in variables
    assert msg
    assert_equal(msg['from'], 'somedude@localhost')
    assert_equal(msg['to'], 'zed.shaw@gmail.com')
    assert_equal(msg['subject'], "This is a respond Test")


def test_HtmlMail_content_type_respected():
    generator = html.HtmlMail("style.css", "html_test.html", {})

    resp = generator.respond({}, "content.markdown",
                           From="somedude@localhost",
                           To="somedude@localhost",
                           Subject="Test of an HTML mail.",
                           Body="content.markdown"
                           )

    req = mail.MailRequest('fakepeer', None, None, str(resp))
    
    assert_equal(req.base.content_encoding['Content-Type'][0], 'multipart/alternative')

    resp2 = mail.MailResponse(To=req['to'],
                              From=req['from'],
                              Subject=req['subject'])
    resp2.attach_all_parts(req)
    
    assert_equal(resp2.base.content_encoding['Content-Type'],
                 resp.base.content_encoding['Content-Type'])
    
    assert_equal(resp2.base.content_encoding['Content-Type'][0], 'multipart/alternative')

    req2 = mail.MailRequest('fakepeer', None, None, str(resp2))

    assert_equal(resp2.base.content_encoding['Content-Type'][0], 'multipart/alternative')

    assert_equal(req2.base.content_encoding['Content-Type'][0], 'multipart/alternative')

