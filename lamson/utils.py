"""
Mostly utility functions Lamson uses internally that don't
really belong anywhere else in the modules.  This module
is kind of a dumping ground, so if you find something that
can be improved feel free to work up a patch.
"""

from lamson import server, routing
import sys, os
import logging
import daemon

try:
    from daemon import pidlockfile 
except:
    from lockfile import pidlockfile 

import imp
import signal


def import_settings(boot_also, from_dir=None, boot_module="config.boot"):
    """Used to import the settings in a Lamson project."""
    if from_dir:
        sys.path.append(from_dir)

    # Assumes that the settings.py has the same parent module as boot.py
    # ie config.boot -> config.settings (just changes the name of the last module)
    settings_module = ".".join( [ boot_module.rsplit(".", 1)[0], "settings" ] )

    settings = __import__(settings_module, globals(), locals()).settings

    if boot_also:
        __import__(boot_module, globals(), locals())

    return settings


def daemonize(pid, chdir, chroot, umask, files_preserve=None, do_open=True):
    """
    Uses python-daemonize to do all the junk needed to make a
    server a server.  It supports all the features daemonize
    has, except that chroot probably won't work at all without
    some serious configuration on the system.
    """
    context = daemon.DaemonContext()
    context.pidfile = pidlockfile.PIDLockFile(pid)
    context.stdout = open(os.path.join(chdir, "logs/lamson.out"),"a+")                                                                                                       
    context.stderr = open(os.path.join(chdir, "logs/lamson.err"),"a+")                                                                                                       
    context.files_preserve = files_preserve or []
    context.working_directory = os.path.expanduser(chdir)

    if chroot: 
        context.chroot_directory = os.path.expanduser(chroot)
    if umask != False:
        context.umask = umask

    if do_open:
        context.open()

    return context

def drop_priv(uid, gid):
    """
    Changes the uid/gid to the two given, you should give utils.daemonize
    0,0 for the uid,gid so that it becomes root, which will allow you to then
    do this.
    """
    logging.debug("Dropping to uid=%d, gid=%d", uid, gid)
    daemon.daemon.change_process_owner(uid, gid)
    logging.debug("Now running as uid=%d, gid=%d", os.getgid(), os.getuid())



def make_fake_settings(host, port):
    """
    When running as a logging server we need a fake settings module to work with
    since the logging server can be run in any directory, so there may not be
    a config/settings.py file to import.
    """
    logging.basicConfig(filename="logs/logger.log", level=logging.DEBUG)
    routing.Router.load(['lamson.handlers.log', 'lamson.handlers.queue'])
    settings = imp.new_module('settings')
    settings.receiver = server.SMTPReceiver(host, port)
    settings.relay = None
    logging.info("Logging mode enabled, will not send email to anyone, just log.")

    return settings

def check_for_pid(pid, force):
    """Checks if a pid file is there, and if it is sys.exit.  If force given
    then it will remove the file and not exit if it's there."""
    if os.path.exists(pid):
        if not force:
            print "PID file %s exists, so assuming Lamson is running.  Give -FORCE to force it to start." % pid
            sys.exit(1)
            return # for unit tests mocking sys.exit
        else:
            os.unlink(pid)


def start_server(pid, force, chroot, chdir, uid, gid, umask, settings_loader, debug):
    """
    Starts the server by doing a daemonize and then dropping priv
    accordingly.  It will only drop to the uid/gid given if both are given.
    """
    check_for_pid(pid, force)

    if not debug:
        daemonize(pid, chdir, chroot, umask, files_preserve=[])

    sys.path.append(os.getcwd())

    settings = settings_loader()

    if uid and gid:
        drop_priv(uid, gid) 
    elif uid or gid:
        logging.warning("You probably meant to give a uid and gid, but you gave: uid=%r, gid=%r.  Will not change to any user.", uid, gid)

    settings.receiver.start()

    if debug:
        print "Lamson started in debug mode. ctrl-c to quit..."
        import time
        try:
            while True:
                time.sleep(100000)
        except KeyboardInterrupt:
            # hard quit, since receiver starts a new thread. dirty but works
            os._exit(1)
