from lxml import etree, sax
from xml.sax.handler import ContentHandler, EntityResolver

# stolen from http://code.activestate.com/recipes/148061/
def wrap(text, width):
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )


class TextOnlyContentHandler(ContentHandler):
    def __init__(self):
        self.text = []
        self.stack = []
        self.links = []

    def startElementNS(self, name, qname, attributes):
        if qname in ["h1", "h2", "h3"]:
            self.stack.append((qname, ""))
        elif qname == "a":
            href = attributes.getValueByQName("href")
            self.stack.append((qname, href))
        elif qname == "p":
            if self.stack:
                self.text.append(self.stack.pop()[1])
            self.text.append("\n\n")

    def characters(self, text_data):
        if text_data.strip():
            data = " ".join([l.strip() for l in text_data.split("\n")]).strip()

            if self.stack:
                qname, text = self.stack.pop()
                if qname in ["h1","h2","h3"]:
                    self.text.append("\n\n" + data + "\n" + "=" * len(data) + "\n")
                elif qname == "a":
                    if text not in self.links:
                        self.links.append(text)

                    index = self.links.index(text)
                    self.text.append(data + "[%d]" % len(self.links))
                else:
                    self.text.append(text + " " + data)
            else:
                self.text.append(data)


def strip_html(doc):
    tree = etree.fromstring(doc)
    handler = TextOnlyContentHandler()
    sax.saxify(tree, handler)
    links_list = ""
    for i, link in enumerate(handler.links):
        links_list += "\n[%d] %s" % (i+1, link)

    text = " ".join(handler.text)
    return wrap(text, 72) + "\n\n----" + links_list


