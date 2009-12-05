import sys
sys.path.append(".")

from lamson.mail import MailRequest, MailResponse
from lamson.queue import Queue
import config.testing
from app.model import archive
import os


def convert_queue(arg, dirname, names):
    if dirname.endswith("new"):
        print dirname, names

        jpath = dirname + "/../../json"
        if not os.path.exists(jpath):
            os.mkdir(jpath)

        for key in names:
            json_file = key + ".json"
            json_archive = os.path.join(jpath, json_file)

            fpath = os.path.join(dirname, key)
            msg = MailRequest('librelist.com', None, None, open(fpath).read())
            f = open(json_archive, "w")
            f.write(archive.to_json(msg.base))
            f.close()

os.path.walk("app/data/archives", convert_queue, None)

