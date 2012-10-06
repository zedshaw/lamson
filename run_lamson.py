from modargs import args

import os, sys
print os.getcwd()

from lamson import commands
import sys

args.parse_and_run_command(sys.argv[1:], commands, default_command="help")

