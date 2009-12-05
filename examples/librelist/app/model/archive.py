from __future__ import with_statement
from lamson import queue
from config import settings
from datetime import datetime
import os
import shutil
import simplejson as json
import base64
import stat

ALLOWED_HEADERS = set([
 "From", "In-Reply-To", "List-Id",
 "Precedence", "References", "Reply-To",
 "Return-Path", "Sender",
 "Subject", "To", "Message-Id",
 "Date", "List-Id",
])

DIR_MOD = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
FILE_MOD = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH

def day_of_year_path():
    return "%d/%0.2d/%0.2d" % datetime.today().timetuple()[0:3]

def store_path(list_name, name):
    datedir = os.path.join(settings.ARCHIVE_BASE, list_name, day_of_year_path())

    if not os.path.exists(datedir):
        os.makedirs(datedir)

    return os.path.join(datedir, name)

def fix_permissions(path):
    os.chmod(path, DIR_MOD)

    for root, dirs, files in os.walk(path):
        os.chmod(root, DIR_MOD)
        for f in files:
            os.chmod(os.path.join(root, f), FILE_MOD)

def update_json(list_name, key, message):
    jpath = store_path(list_name, 'json')
    json_file = key + ".json"
    json_archive = os.path.join(jpath, json_file)

    if not os.path.exists(jpath):
        os.makedirs(jpath)

    with open(json_archive, "w") as f:
        f.write(to_json(message.base))

    fix_permissions(jpath)


def enqueue(list_name, message):
    qpath = store_path(list_name, 'queue')
    pending = queue.Queue(qpath, safe=True)
    white_list_cleanse(message)

    key = pending.push(message)
    fix_permissions(qpath)

    update_json(list_name, key, message)
    return key

def white_list_cleanse(message):
    for key in message.keys():
        if key not in ALLOWED_HEADERS:
            del message[key]

    message['from'] = message['from'].replace(u'@',u'-AT-')
   

def json_encoding(base):
    ctype, ctp = base.content_encoding['Content-Type']
    cdisp, cdp = base.content_encoding['Content-Disposition']
    ctype = ctype or "text/plain"
    filename = ctp.get('name',None) or cdp.get('filename', None)

    if ctype.startswith('text') or ctype.startswith('message'):
        encoding = None
    else:
        encoding = "base64"

    return {'filename': filename, 'type': ctype, 'disposition': cdisp,
            'format': encoding}

def json_build(base):
    data = {'headers': base.headers,
                'body': base.body,
                'encoding': json_encoding(base),
                'parts': [json_build(p) for p in base.parts],
            }

    if data['encoding']['format'] and base.body:
        data['body'] = base64.b64encode(base.body)

    return data

def to_json(base):
    return json.dumps(json_build(base), sort_keys=True, indent=4)

