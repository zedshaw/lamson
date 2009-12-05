#!/usr/bin/env python
from __future__ import with_statement

import os
import sys
import string
from string import Template
from config import *
from datetime import date
from textile import textile
from stat import *
import datetime
import PyRSS2Gen

rss = PyRSS2Gen.RSS2(
    title = options["sitename"],
    link = options["siteurl"],
    description = options["slogan"],
    lastBuildDate = datetime.datetime.now(),
    items = [])


def add_rss_item(rss, title, link, description, pubDate):
       item = PyRSS2Gen.RSSItem(title = title, link = link,
         description = description,
         guid = PyRSS2Gen.Guid(link),
         pubDate = datetime.datetime.fromtimestamp(pubDate))
       rss.items.append(item)

def ext(fname):
    return os.path.splitext(fname)[1]

def process(fname):
    with open(fname, 'r') as f:
        try:
            head, body = f.read().split('\n\n')
            body
        except:
            print 'Invalid file format : ', fname

def parse(fname):
    with open(fname, 'r') as f:
        raw = f.read()
        headers = {}
        try:
            (header_lines,body) = raw.split("\n\n", 1)
            for header in header_lines.split("\n"):
                (name, value) = header.split(": ", 1)
                headers[name.lower()] = unicode(value.strip())
            return headers, body
        except:
            raise TypeError, "Invalid page file format for %s" % fname

           
def get_template(template):
    """Takes the directory where templates are located and the template name. Returns a blob containing the template."""
    template = os.path.join(template_dir, template)

    return Template(open(template, 'r').read())
       
def source_newer(source, target):
    if len(sys.argv) > 1 and sys.argv[1] == "force":
        return True

    if not os.path.exists(target): 
        return True
    else:
        smtime = os.stat(source)[ST_MTIME]
        tmtime = os.stat(target)[ST_MTIME]
        return smtime > tmtime

def is_blog(current_dir, myself, headers, files):
    """A page tagged as an entry will get the files, sort them by their dates,
    and then the contents will be that directory listing instead."""
    
    if 'content-type' in headers and headers['content-type'] == "text/blog":
        # it's a listing, make it all work
        without_self = files[:]
        without_self.remove(os.path.split(myself)[-1])
        without_self.sort(reverse=True)

        listing = []
        for f in without_self:
            print "Doing blog", f
            # load up the file and peel out the first few paragraphs
            content = os.path.join(current_dir, f)
            head, body = parse(content)
            paras = [p for p in body.split("\n\n") if p]
            if paras:
                # now make a simple listing entry with it
                date, ext = os.path.splitext(f)
                head["link"] = os.path.join("/" + os.path.split(current_dir)[-1], date + ".html")
                head["date"] = date
                format = determine_format(head)
                pubDate = smtime = os.stat(content)[ST_CTIME]
                head["content"] = content_format(current_dir, f, head, files,
                                                 format, "\n\n".join(paras[0:1]))
                template = head['item-template'] if 'item-template' in head else headers['item-template']
                description = get_template(template).safe_substitute(head)

                if "feed" not in headers:
                    add_rss_item(rss, head["title"], options["siteurl"] +
                                 head["link"], description, pubDate)
                listing.append(description)

        return lambda s: "".join(listing)
    else:
        return lambda s: s

def content_format(current_dir, inp, headers, files, format, body):
    return {
            u'text/plain': lambda s: u'<pre>%s</pre>' % s,
            u'text/x-textile':  lambda s: u'%s' % textile(s,head_offset=0, validate=0, 
                                sanitize=0, encoding='utf-8', output='utf-8'),
            u'text/html': lambda s: s,
            u'text/blog': is_blog(current_dir, inp, headers, files)
        }[format](body)

def determine_format(headers):
    if 'content-type' in headers:
        return headers['content-type']
    else:
        return options['format']

def parse_directory(current_dir, files, output_dir):
    files = [f for f in files if ext(f) in options['extensions']]
    for f in files:
        inp = os.path.join(current_dir, f)
        target = os.path.join(output_dir, f)
        # TODO: Allow specifying the target extension from headers
        outp = os.path.splitext(target)[0] + '.html'

        # always redo the indexes since they'll typically list information to
        # update from the directory they are in
        if not source_newer(inp, outp) and f != "index.txt":
            continue

        headers, body = parse(inp)

        if 'template' not in headers:
            blob = get_template(template)
        else:
            blob = get_template(headers['template'])

        format = determine_format(headers)

        print "Processing %s" % inp

        content = content_format(current_dir, inp, headers, files, format, body)
        
        headers['content'] = content
        headers.update(options)
        output = blob.safe_substitute(**headers)

        outf = open(outp, 'w')
        outf.write(output)
        outf.close()

def a_fucking_cmp_for_time(x,y):
    diff = y.pubDate - x.pubDate
    return diff.days * 24 * 60 * 60 + diff.seconds

def main():
    ### Walks through the input dir creating finding all subdirectories.
    for root, dirs, files in os.walk(input_dir):
        output = root.replace(input_dir, output_dir)
        ### Checks if the directory exists in output and creates it if false.
        if not os.path.isdir(output):
            os.makedirs(output)

        parse_directory(root, files, output)

    x,y = rss.items[0], rss.items[-1]
    diff = x.pubDate - y.pubDate
    print "diff!", diff.seconds, diff.days
    rss.items.sort(cmp=lambda x,y: a_fucking_cmp_for_time(x,y))
    rss.write_xml(open("output/feed.xml", "w"))

    
if __name__ == '__main__':
    main()
