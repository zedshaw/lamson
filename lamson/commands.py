"""
Implements the Lamson command line tool's commands, which are run
by the lamson.args module dynamically.  Each command has it's
actual user displayed command line documentation as the __doc__
string.

You will notice that all of the command functions in this module
end in _command.  This is not required by the lamson.args module
but it is the default.  You could easily use any other suffix, or
none at all.

This is done to disambiguate the command that it implements
so that your command line tools do not clash with Python's
reserved words and built-ins.  With this design you can have a
list_command without clashing with list().

You will also notice that commands which take trailing positional
arguments give a TRAILING=[] or TRAILING=None (if it's required).
This is done instead of *args because we need to use None to indicate
that this command requires positional arguments.  TRAILING=[] is 
like saying they are optional (but expected), and TRAILING=None is
like saying they are required.  You can't (afaik) do TRAILING=None
with *args.

See python-modargs for more details.
"""

from lamson import server, utils, mail, routing, queue, encoding
from modargs import args
from pkg_resources import resource_stream
from zipfile import ZipFile
import glob
import lamson
import os
import signal
import sys
import time
import mailbox
import email

def log_command(port=8825, host='127.0.0.1', chroot=False,
                chdir=".", uid=False, gid=False, umask=False, pid="./run/log.pid",
               FORCE=False, debug=False):
    """
    Runs a logging only server on the given hosts and port.  It logs
    each message it receives and also stores it to the run/queue 
    so that you can make sure it was received in testing.

    lamson log -port 8825 -host 127.0.0.1 \\
            -pid ./run/log.pid -chroot False  \\
            -chdir "." -umask False -uid False -gid False \\
            -FORCE False

    If you specify a uid/gid then this means you want to first change to
    root, set everything up, and then drop to that UID/GID combination.
    This is typically so you can bind to port 25 and then become "safe"
    to continue operating as a non-root user.

    If you give one or the other, this it will just change to that
    uid or gid without doing the priv drop operation.
    """
    loader = lambda: utils.make_fake_settings(host, port)
    utils.start_server(pid, FORCE, chroot, chdir, uid, gid, umask, loader, debug)


def send_command(port=8825, host='127.0.0.1', username=False, password=False,
                 ssl=False, starttls=False, debug=1, sender=None, to=None,
                 subject=None, body=None, attach=False):
    """
    Sends an email to someone as a test message.
    See the sendmail command for a sendmail replacement.
    
    lamson send -port 8825 -host 127.0.0.1 -debug 1 \\
            -sender EMAIL -to EMAIL -subject STR -body STR -attach False'

    There is also a username, password, and starttls option for those 
    who need it.
    """
    message = mail.MailResponse(From=sender,
                                  To=to,
                                  Subject=subject,
                                  Body=body)
    if attach:
        message.attach(attach)

    if username == False:
        username = None
    if password == False:
        password = None

    relay = server.Relay(host, port=port, username=username, password=password,
                         ssl=ssl, starttls=starttls, debug=debug)
    relay.deliver(message)


def sendmail_command(port=8825, host='127.0.0.1', debug=0, TRAILING=None):
    """
    Used as a testing sendmail replacement for use in programs
    like mutt as an MTA.  It reads the email to send on the stdin
    and then delivers it based on the port and host settings.

    lamson sendmail -port 8825 -host 127.0.0.1 -debug 0 -- [recipients]
    """
    relay = server.Relay(host, port=port,
                           debug=debug)
    data = sys.stdin.read()
    msg = mail.MailRequest(Peer=None, From=None, To=None, Data=data)
    relay.deliver(msg, To=TRAILING)




def start_command(pid='./run/smtp.pid', FORCE=False, chroot=False, chdir=".",
                  boot="config.boot", uid=False, gid=False, umask=False, debug=False):
    """
    Runs a lamson server out of the current directory:

    lamson start -pid ./run/smtp.pid -FORCE False -chroot False -chdir "." \\
            -umask False -uid False -gid False -boot config.boot
    """
    loader = lambda: utils.import_settings(True, from_dir=os.getcwd(), boot_module=boot)
    utils.start_server(pid, FORCE, chroot, chdir, uid, gid, umask, loader, debug)


def stop_command(pid='./run/smtp.pid', KILL=False, ALL=False):
    """
    Stops a running lamson server.  Give -KILL True to have it
    stopped violently.  The PID file is removed after the 
    signal is sent.  Give -ALL the name of a run directory and
    it will stop all pid files it finds there.

    lamson stop -pid ./run/smtp.pid -KILL False -ALL False
    """
    pid_files = []

    if ALL:
        pid_files = glob.glob(ALL + "/*.pid")
    else:
        pid_files = [pid]

        if not os.path.exists(pid):
            print "PID file %s doesn't exist, maybe Lamson isn't running?" % pid
            sys.exit(1)
            return # for unit tests mocking sys.exit

    print "Stopping processes with the following PID files: %s" % pid_files

    for pid_f in pid_files:
        pid = open(pid_f).readline()

        print "Attempting to stop lamson at pid %d" % int(pid)

        try:
            if KILL:
                os.kill(int(pid), signal.SIGKILL)
            else:
                os.kill(int(pid), signal.SIGHUP)
            
            os.unlink(pid_f)
        except OSError, exc:
            print "ERROR stopping Lamson on PID %d: %s" % (int(pid), exc)


def restart_command(**options):
    """
    Simply attempts a stop and then a start command.  All options for both
    apply to restart.  See stop and start for options available.
    """

    stop_command(**options)
    time.sleep(2)
    start_command(**options)


def status_command(pid='./run/smtp.pid'):
    """
    Prints out status information about lamson useful for finding out if it's
    running and where.

    lamson status -pid ./run/smtp.pid
    """
    if os.path.exists(pid):
        pid = open(pid).readline()
        print "Lamson running with PID %d" % int(pid)
    else:
        print "Lamson not running."


def help_command(**options):
    """
    Prints out help for the commands. 

    lamson help

    You can get help for one command with:

    lamson help -for STR
    """
    if "for" in options:
        help_text = args.help_for_command(lamson.commands, options['for'])
        if help_text:
            print help_text
        else:
            args.invalid_command_message(lamson.commands, exit_on_error=True)
    else:
        print "Available commands:\n"
        print ", ".join(args.available_commands(lamson.commands))
        print "\nUse lamson help -for <command> to find out more."


def queue_command(pop=False, get=False, keys=False, remove=False, count=False,
                  clear=False, name="run/queue"):
    """
    Let's you do most of the operations available to a queue.

    lamson queue (-pop | -get | -remove | -count | -clear | -keys) -name run/queue
    """
    print "Using queue: %r" % name

    inq = queue.Queue(name)

    if pop:
        key, msg = inq.pop()
        if key:
            print "KEY: ", key
            print msg
    elif get:
        print inq.get(get)
    elif remove:
        inq.remove(remove)
    elif count:
        print "Queue %s contains %d messages" % (name, inq.count())
    elif clear:
        inq.clear()
    elif keys:
        print "\n".join(inq.keys())
    else:
        print "Give something to do.  Try lamson help -for queue to find out what."
        sys.exit(1)
        return # for unit tests mocking sys.exit
        

def routes_command(TRAILING=['config.testing'], path=os.getcwd(), test=""):
    """
    Prints out valuable information about an application's routing configuration
    after everything is loaded and ready to go.  Helps debug problems with
    messages not getting to your handlers.  Path has the search paths you want
    separated by a ':' character, and it's added to the sys.path.

    lamson routes -path $PWD -- config.testing -test ""

    It defaults to running your config.testing to load the routes. 
    If you want it to run the config.boot then give that instead:

    lamson routes -- config.boot

    You can also test a potential target by doing -test EMAIL.

    """
    modules = TRAILING
    sys.path += path.split(':')
    test_case_matches = []

    for module in modules:
        __import__(module, globals(), locals())

    print "Routing ORDER: ", routing.Router.ORDER
    print "Routing TABLE: \n---"
    for format in routing.Router.REGISTERED:
        print "%r: " % format,
        regex, functions = routing.Router.REGISTERED[format]
        for func in functions:
            print "%s.%s " % (func.__module__, func.__name__),
            match = regex.match(test)
            if test and match:
                test_case_matches.append((format, func, match))

        print "\n---"

    if test_case_matches:
        print "\nTEST address %r matches:" % test
        for format, func, match in test_case_matches:
            print "  %r %s.%s" % (format, func.__module__, func.__name__)
            print "  -  %r" % (match.groupdict())
    elif test:
        print "\nTEST address %r didn't match anything." % test



def gen_command(project=None, FORCE=False):
    """
    Generates various useful things for you to get you started.

    lamson gen -project STR -FORCE False
    """
    project = project

    if os.path.exists(project) and not FORCE:
        print "Project %s exists, delete it first." % project
        sys.exit(1)
        return

    prototype = ZipFile(resource_stream(__name__, 'data/prototype.zip'))
    # looks like the very handy ZipFile.extractall is only in python 2.6

    if not os.path.exists(project):
        os.makedirs(project)

    files = prototype.namelist()

    for gen_f in files:
        if str(gen_f).endswith('/'):
            target = os.path.join(project, gen_f)
            if not os.path.exists(target):
                print "mkdir: %s" % target
                os.makedirs(target)
        else:
            target = os.path.join(project, gen_f)
            if os.path.exists(target): 
                continue

            print "copy: %s" % target
            out = open(target, 'w')
            out.write(prototype.read(gen_f))
            out.close()


def web_command(basedir=".", port=8888, host='127.0.0.1'):
    """
    Starts a very simple files only web server for easy testing of applications
    that need to make some HTML files as the result of their operation.
    If you need more than this then use a real web server.

    lamson web -basedir "." -port 8888 -host '127.0.0.1'

    This command doesn't exit so you can view the logs it prints out.
    """
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler 

    os.chdir(basedir)
    web = HTTPServer((host, port), SimpleHTTPRequestHandler)
    print "Starting server on %s:%d out of directory %r" % (
        host, port, basedir)
    web.serve_forever()


def cleanse_command(input=None, output=None):
    """
    Uses Lamson mail cleansing and canonicalization system to take an
    input maildir (or mbox) and replicate the email over into another
    maildir.  It's used mostly for testing and cleaning.
    """
    error_count = 0

    try:
        inbox = mailbox.mbox(input)
    except:
        inbox = mailbox.Maildir(input, factory=None)

    outbox = mailbox.Maildir(output)

    for msg in inbox:
        try:
            mail = encoding.from_message(msg)
            outbox.add(encoding.to_string(mail))
        except encoding.EncodingError, exc:
            print "ERROR: ", exc
            error_count += 1

    outbox.close()
    inbox.close()

    print "TOTAL ERRORS:", error_count


def blast_command(input=None, host='127.0.0.1', port=8823, debug=0):
    """
    Given a maildir, this command will go through each email
    and blast it at your server.  It does nothing to the message, so
    it will be real messages hitting your server, not cleansed ones.
    """
    inbox = mailbox.Maildir(input)
    relay = server.Relay(host, port=port, debug=debug)

    for key in inbox.keys():
        msgfile = inbox.get_file(key)
        msg = email.message_from_file(msgfile)
        relay.deliver(msg)


def version_command():
    """
    Prints the version of Lamson, the reporitory revision, and the
    file it came from.
    """

    from lamson import version

    print "Lamson-Version: ", version.VERSION['version']
    print "Repository-Revision:", version.VERSION['rev'][0]
    print "Repository-Hash:", version.VERSION['rev'][1]
    print "Version-File:", version.__file__
    print ""
    print "Lamson is Copyright (C) Zed A. Shaw 2008-2009.  Licensed GPLv3."
    print "If you didn't get a copy of the LICENSE contact the author at:\n"
    print "   zedshaw@zedshaw.com"
    print ""
    print "Have fun."

