"""
These are helper functions that make it easier to work with either
Jinja2 or Mako templates.  You MUST configure it by setting
lamson.view.LOADER to one of the template loaders in your config.boot
or config.testing.

After that these functions should just work.
"""

from lamson import mail
import email
import warnings

LOADER = None

def load(template):
    """
    Uses the registered loader to load the template you ask for.
    It assumes that your loader works like Jinja2 or Mako in that
    it has a LOADER.get_template() method that returns the template.
    """
    assert LOADER, "You haven't set lamson.view.LOADER to a loader yet."
    return LOADER.get_template(template)


def render(variables, template):
    """
    Takes the variables given and renders the template for you.
    Assumes the template returned by load() will have a .render()
    method that takes the variables as a dict.

    Use this if you just want to render a single template and don't
    want it to be a message.  Use render_message if the contents
    of the template are to be interpreted as a message with headers
    and a body.
    """
    return load(template).render(variables)


def respond(variables, Body=None, Html=None, **kwd):
    """
    Does the grunt work of cooking up a MailResponse that's based
    on a template.  The only difference from the lamson.mail.MailResponse
    class and this (apart from variables passed to a template) are that
    instead of giving actual Body or Html parameters with contents,
    you give the name of a template to render.  The kwd variables are
    the remaining keyword arguments to MailResponse of From/To/Subject.

    For example, to render a template for the body and a .html for the Html
    attachment, and to indicate the From/To/Subject do this:

        msg = view.respond(locals(), Body='template.txt', 
                          Html='template.html',
                          From='test@test.com',
                          To='receiver@test.com',
                          Subject='Test body from "%(dude)s".')

    In this case you're using locals() to gather the variables needed for
    the 'template.txt' and 'template.html' templates.  Each template is
    setup to be a text/plain or text/html attachment.  The From/To/Subject
    are setup as needed.  Finally, the locals() are also available as
    simple Python keyword templates in the From/To/Subject so you can pass
    in variables to modify those when needed (as in the %(dude)s in Subject).
    """

    assert Body or Html, "You need to give either the Body or Html template of the mail."

    for key in kwd:
        kwd[key] = kwd[key] % variables
    
    msg = mail.MailResponse(**kwd)

    if Body:
        msg.Body = render(variables, Body)
    
    if Html:
        msg.Html = render(variables, Html)

    return msg


def attach(msg, variables, template, filename=None, content_type=None,
           disposition=None):
    """
    Useful for rendering an attachment and then attaching it to the message
    given.  All the parameters that are in lamson.mail.MailResponse.attach
    are there as usual.
    """
    data = render(variables, template)

    msg.attach(filename=filename, data=data, content_type=content_type,
               disposition=disposition)

