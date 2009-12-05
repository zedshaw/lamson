from nose.tools import *
from lamson import utils, view
from mock import *


def test_make_fake_settings():
    settings = utils.make_fake_settings('localhost', 8800)
    assert settings
    assert settings.receiver
    assert settings.relay == None
    settings.receiver.close()

def test_import_settings():
    loader = view.LOADER

    settings = utils.import_settings(True, from_dir='tests', boot_module='config.testing')
    assert settings
    assert settings.receiver_config

    view.LOADER = loader
    settings = utils.import_settings(False, from_dir='examples/osb')
    assert settings
    assert settings.receiver_config



@patch('daemon.DaemonContext.open')
def test_daemonize_not_fully(dc_open):
    context = utils.daemonize("run/tests.pid", ".", False, False, do_open=False)
    assert context
    assert not dc_open.called
    dc_open.reset_mock()

    context = utils.daemonize("run/tests.pid", ".", "/tmp", 0002, do_open=True)
    assert context
    assert dc_open.called


@patch("daemon.daemon.change_process_owner")
def test_drop_priv(cpo):
    utils.drop_priv(100, 100)
    assert cpo.called

