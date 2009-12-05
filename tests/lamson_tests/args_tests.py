from nose.tools import *
import os
from lamson import args, commands
from mock import *
import sys



def test_match():
    tokens = [["word", "test"],["int", 1]]
    assert args.match(tokens, "word") == "test", "Wrong word on match."
    assert args.match(tokens) == 1, "Wrong int on match."

    assert len(tokens) == 0, "There should be nothing in the array after matching."


@raises(args.ArgumentError)
def test_match_fails():
    tokens = [["word", "test"],["int", 1]]
    args.match(tokens, "string")



def test_peek():
    tokens = [["word", "test"],["int", 1]]
    assert args.peek(tokens, "word"), "There should be a word."
    assert len(tokens) == 2, "Args should not go down after peek."
    args.match(tokens, "word")

    assert args.peek(tokens, "int"), "There should be an int."
    assert not args.peek(tokens, "option"), "There should not be an option."
    args.match(tokens, "int")

@raises(args.ArgumentError)
def test_peek_fails():
    tokens = []
    args.peek(tokens, 'string')

def test_determine_kwargs():
    kw = args.determine_kwargs(commands.log_command)
    assert kw['pid']

def test_tokenize():
    tokens = args.tokenize(['test', '--num', '1', '--help', '--stuff', 'The remainder.'])
    assert args.match(tokens, 'word')
    assert args.match(tokens, 'option')
    assert args.match(tokens, 'int')
    assert args.match(tokens, 'option')
    assert args.match(tokens, 'option')
    assert args.match(tokens, 'string')

    # test a condition where there is a remainder that's not identified
    tokens = args.tokenize(['stop', '--pid', 'run/log.pid'])
    assert tokens
    assert args.match(tokens, 'word')
    assert args.match(tokens, 'option')
    assert args.match(tokens, 'string')


def test_parse():
    command, options = args.parse(['test', '--num', '1', '--help', '--stuff', 'The remainder.', '--tail'])
    assert command, "There should be a command."
    assert options, "There should be options."

    assert command == "test", "command should be test"
    assert options["num"] == 1, "num option wrong"
    assert options["help"] == True, "help should be true"
    assert options["stuff"] == 'The remainder.', "stuff should a string"
    assert options['tail'] == True, "There should be a True tail."

    command2, options = args.parse(['--num', '1', '--help', '--stuff', 'The remainder.'])
    assert not command2, "There should NOT be a command."
    assert options, "There should be options."
    assert options["num"] == 1, "num option wrong"
    assert options["help"] == True, "help should be true"
    assert options["stuff"] == 'The remainder.', "stuff should a string"


def test_defaults():
    command, options = args.parse(['test', '--num', '1', '--help', '--stuff', 'The remainder.'])
    args.ensure_defaults(options, {'num': 2, 'help': True, 'stuff': None})
    assert options['help'] == True
    assert options['num'] == 1
   
    command, options = args.parse(['test', '--num', '1', '--help', '--stuff', 'The remainder.'])
    args.ensure_defaults(options, {'num': 2, 'extras': 3, 'help': None, 
                                   'stuff': None})
    assert options['extras'] == 3
    assert options['num'] == 1


    assert_raises(args.ArgumentError,
                  args.ensure_defaults,
                  options, {'num': 2, 'extras': 3, 'help': None, 'TRAILING': None})

    assert_raises(args.ArgumentError,
                  args.ensure_defaults,
                  options, {'num': 2, 'extras': 3, 'help': None, 'bad': None})

def test_available_help():
    assert args.available_help(commands)    

def test_available_commands():
    assert args.available_commands(commands).index('help') >= 0, 'no help command'

@patch('sys.exit', new=Mock())
def test_parse_and_run_command():
    assert args.parse_and_run_command(['help'], commands,
                                      default_command=None)

    assert not args.parse_and_run_command(['badcommand'], commands,
                                      default_command=None, exit_on_error=False)
    assert not sys.exit.called

    assert not args.parse_and_run_command(['badcommand'], commands,
                                      default_command=None, exit_on_error=True)
    assert sys.exit.called

    assert not args.parse_and_run_command(['badcommand'], commands,
                                      default_command='help', exit_on_error=False)

    assert args.parse_and_run_command([], commands,
                                      default_command='send', exit_on_error=False)

    assert args.parse_and_run_command([], commands,
                                      default_command='help', exit_on_error=False)


def test_help_for_command():
    assert args.help_for_command(commands, "help")
    assert not args.help_for_command(commands, "badcommand")

def test_trailing():
    command, options = args.parse(['test', '--num', '1', '--', 'Trailing 1', 'Trailing 2'])
    expected = ['Trailing 1', 'Trailing 2']
    assert command == 'test'
    assert options['TRAILING']
    for e in expected: assert e in options['TRAILING']

    # test with a corner case of a switch option before trailing
    command, options = args.parse(['test', '--num', '1', '--switch', '--', 'Trailing 1', 'Trailing 2'])
    for e in expected: assert e in options['TRAILING']


@patch('sys.exit', new=Mock())
def test_invalid_options():
    args.parse_and_run_command(['log -foobar'], commands)

    args.parse_and_run_command(['log badarg'], commands)
    assert sys.exit.called

def test_no_command_or_default():
    args.parse_and_run_command([], commands,
                                      default_command=None,
                                      exit_on_error=False)

