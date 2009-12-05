"""
This implements an HTML Mail generator that uses templates and CleverCSS
to produce an HTML message with inline CSS attributes so that it will
display correctly.  As long as you can keep most of the HTML and CSS simple you
should have a high success rate at rendering this.

How it works is you create an HtmlMail class and configure it with a CleverCSS
stylesheet (also a template).  This acts as your template for the appearance and
the outer shell of your HTML.

When you go to send, you use a markdown content template to generate the
guts of your HTML.  You hand this, variables, and email headers to 
HtmlMail.respond and it spits back a fully formed lamson.mail.MailResponse
ready to send.

The engine basically parses the CSS, renders your content template, 
render your outer template, and then applies the CSS directly to your HTML
so your CSS attributes are inline and display in the HTML display.

Each element is a template loaded by your loader: the CleverCSS template, out HTML
template, and your own content.

Finally, use this as a generator by making one and having crank out all the emails
you need.  Don't make one HtmlMail for each message.
"""

from BeautifulSoup import BeautifulSoup
import clevercss
from lamson import mail, view
from markdown2 import markdown


class HtmlMail(object):
    """
    Acts as a lamson.mail.MailResponse generator that produces a properly 
    formatted HTML mail message, including inline CSS applied to all HTML tags.
    """
    def __init__(self, css_template, html_template, variables={}, wiki=markdown):
        """
        You pass in a CleverCSS template (it'll be run through the template engine
        before CleverCSS), the html_template, and any variables that the CSS template
        needs.

        The CSS template is processed once, the html_template is processed each time
        you call render or respond.

        If you don't like markdown, then you can set the wiki variable to any callable
        that processes your templates.
        """
        self.template = html_template
        self.load_css(css_template, variables)
        self.wiki = wiki

    def load_css(self, css_template, variables):
        """
        If you want to change the CSS, simply call this with the new CSS and variables.
        It will change internal state so that later calls to render or respond use
        the new CSS.
        """
        self.css = view.render(variables, css_template)
        self.engine = clevercss.Engine(self.css)
        self.stylesheet = []
        
        for selector, style in self.engine.evaluate():
            attr = "; ".join("%s: %s" % (k,v) for k,v in style)
            selectors = selector[0].split()
            # root, path, attr
            self.stylesheet.append((selectors[0], selectors[1:], attr))


    def reduce_tags(self, name, tags):
        """
        Used mostly internally to find all the tags that fit the given
        CSS selector.  It's fairly primitive, working only on tag names,
        classes, and ids.  You shouldn't get too fancy with the CSS you create.
        """
        results = []

        for tag in tags:
            if name.startswith("#"):
                children = tag.findAll(attrs={"class": name[1:]})
            elif name.startswith("."):
                children = tag.findAll(attrs={"id": name[1:]})
            else:
                children = tag.findAll(name)

            if children:
                results += children

        return results

    def apply_styles(self, html):
        """
        Used mostly internally but helpful for testing, this takes the given HTML
        and applies the configured CSS you've set.  It returns a BeautifulSoup
        object with all the style attributes set and nothing else changed.
        """
        doc = BeautifulSoup(html)
        roots = {}  # the roots rarely change, even though the paths do

        for root, path, attr in self.stylesheet:
            tags = roots.get(root, None)
            
            if not tags:
                tags = self.reduce_tags(root, [doc])
                roots[root] = tags
           
            for sel in path:
                tags = self.reduce_tags(sel, tags)


            for node in tags:
                try:
                    node['style'] += "; " + attr
                except KeyError:
                    node['style'] = attr

        return doc

        
    def render(self, variables, content_template,  pretty=False):
        """
        Works like lamson.view.render, but uses apply_styles to modify
        the HTML with the configured CSS before returning it to you.

        If you set the pretty=True then it will prettyprint the results,
        which is a waste of bandwidth, but helps when debugging.

        Remember that content_template is run through the template system,
        and then processed with self.wiki (defaults to markdown).  This
        let's you do template processing and write the HTML contents like
        you would an email.

        You could also attach the content_template as a text version of the
        message for people without HTML.  Simply set the .Body attribute
        of the returned lamson.mail.MailResponse object.
        """
        content = self.wiki(view.render(variables, content_template))
        lvars = variables.copy()
        lvars['content'] = content

        html = view.render(lvars, self.template)
        styled = self.apply_styles(html)

        if pretty:
            return styled.prettify()
        else:
            return str(styled)


    def respond(self, variables, content, **kwd):
        """
        Works like lamson.view.respond letting you craft a
        lamson.mail.MailResponse immediately from the results of
        a lamson.html.HtmlMail.render call.  Simply pass in the
        From, To, and Subject parameters you would normally pass
        in for MailResponse, and it'll craft the HTML mail for
        you and return it ready to deliver.

        A slight convenience in this function is that if the
        Body kw parameter equals the content parameter, then
        it's assumed you want the raw markdown content to be
        sent as the text version, and it will produce a nice
        dual HTML/text email.
        """
        assert content, "You must give a contents template."

        if kwd.get('Body', None) == content:
            kwd['Body'] = view.render(variables, content)

        for key in kwd:
            kwd[key] = kwd[key] % variables
        
        msg = mail.MailResponse(**kwd)
        msg.Html = self.render(variables, content)

        return msg


    
